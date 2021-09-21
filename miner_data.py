import asyncio
import json
import asyncssh
import base64
import os

# define constants such as the BraiinsOS package to be installed, the update tar file, and the referral ipk
REFERRAL_FILE_S9 = os.path.join("files", "referral.ipk")
LIB_FILE_S9 = os.path.join(os.getcwd(), "files", "system", "ld-musl-armhf.so.1")
SFTP_SERVER_S9 = os.path.join(os.getcwd(), "files", "system", "sftp-server")
FW_PRINTENV_S9 = os.path.join(os.getcwd(), "files", "system", "fw_printenv")
FIRMWARE_PATH_S9 = os.path.join(os.getcwd(), "files", "firmware")
UPDATE_FILE_S9 = os.path.join(os.getcwd(), "files", "update.tar")
CONFIG_FILE = os.path.join(os.getcwd(), "files", "config.toml")
NEWEST_VERSION = "21.04"


class BOSminer:
    def __init__(self, ip: str):
        self.main_state = "start"
        self.stats = None
        self.ip = ip
        self.api_port = 4028
        self.running = asyncio.Event()
        self.running.set()
        self.bos = asyncio.Event()
        self.lit = False
        self.messages = {"IP": self.ip, "text": ""}

    async def ping(self, port: int) -> bool:
        """
        Ping a port on the miner, used by ping_ssh and ping_http
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # open a connection to the miner on specified port
        connection_fut = asyncio.open_connection(self.ip, port)
        try:
            # get the read and write streams from the connection
            reader, writer = await asyncio.wait_for(connection_fut, timeout=1)
            # immediately close connection, we know connection happened
            writer.close()
            # make sure the writer is closed
            await writer.wait_closed()
            # ping was successful
            return True
        except asyncio.exceptions.TimeoutError:
            # ping failed if we time out
            return False
        except ConnectionRefusedError:
            # handle for other connection errors
            self.add_to_output("Unknown error...")
        # ping failed, likely with an exception
        return False

    async def ping_ssh(self) -> bool:
        """
        Ping the SSH port of the miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # ping port 22 (SSH)
        if await self.ping(22):
            # ping returned true, SSH is up
            return True
        else:
            # ping returned false, SSH is down
            return False

    async def ping_http(self) -> bool:
        """
        Ping the HTTP port of the miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # ping port 80 (HTTP)
        if await self.ping(80):
            # ping returned true, HTTP is up
            return True
        else:
            # ping returned false, HTTP is down
            return False

    async def wait_for_disconnect(self) -> None:
        """
        Wait for the miner to disconnect
        """
        self.add_to_output('Waiting for disconnect...')
        while await self.ping_http():
            # pause logic
            if not self.running.is_set():
                self.add_to_output("Paused...")
            await self.running.wait()
            await asyncio.sleep(1)

    async def get_version(self) -> str or bool:
        """
        Get the version of the miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # tell the user we are getting the version
        self.add_to_output("Getting version...")
        retries = 0
        while True:
            # open a connection to the [cgminer, bmminer, bosminer] API port (4028)
            connection_fut = asyncio.open_connection(self.ip, 4028)
            try:
                # get reader and writer streams from connection
                reader, writer = await asyncio.wait_for(connection_fut, timeout=5)
                # send the standard version command (JSON)
                writer.write(b'{"command":"version"}')
                # wait until command is finished sending
                await writer.drain()
                # read the returned data
                data = await reader.read(4096)
                # let the user know we recieved data
                self.add_to_output("Recieved data...")
                # close the writer
                writer.close()
                # make sure the writer is fully closed
                await writer.wait_closed()
                # load the returned data (JSON), and remove the null byte at the end
                data_dict = json.loads(data[:-1].decode('utf-8'))
                # tell the user the version of the miner
                self.add_to_output(f'Version is {data_dict["VERSION"][0][list(data_dict["VERSION"][0].keys())[1]]}...')
                if "BOSminer+" in data_dict["VERSION"][0].keys() or "BOSminer" in data_dict["VERSION"][0].keys():
                    # get/create ssh connection to miner
                    conn = await self.get_connection("root", "admin")
                    # send the command and store the result
                    try:
                        result = await conn.run("cat /etc/bos_version")
                        version_base = result.stdout
                        version_base = version_base.strip()
                        version_base = version_base.split("-")
                        version = version_base[-2]
                        if version == NEWEST_VERSION:
                            return "New"
                        else:
                            return "BOS+"
                    except:
                        return "BOS+"
                else:
                    return "Antminer"
            except asyncio.exceptions.TimeoutError:
                # we have no version, the connection timed out
                self.add_to_output("Get version failed...")
                return False
            except ConnectionRefusedError:
                # add to retry times
                retries += 1
                # connection was refused, tell the user
                self.add_to_output("Connection refused, retrying...")
                # make sure it doesnt get stuck here
                if retries > 3:
                    self.add_to_output('Connection refused, attempting install...')
                    return "Antminer"

    async def send_api_cmd(self, command: str) -> dict or None:
        """Send a command to the API of the miner"""
        try:
            # open reader and writer streams to the api
            reader, writer = await asyncio.open_connection(self.ip, self.api_port)

            # write the command
            api_command = json.dumps({"command": command}).encode('utf-8')

            # send the command
            writer.write(api_command)
            await writer.drain()

            data = b""

            # loop to receive all the data
            while True:
                d = await reader.read(4096)
                if not d:
                    break
                data += d

            # load the data into a dict
            data = json.loads(data.decode('utf-8')[:-1])

            # close the connection
            writer.close()
            await writer.wait_closed()

            # return the data
            return data
        except:
            # if an error happens, return none
            return None

    async def pause(self) -> None:
        """Pause the miner"""
        self.add_to_output("Pausing...")
        self.running.clear()

    async def unpause(self) -> None:
        """Unpause the miner"""
        self.add_to_output("Unpausing...")
        self.running.set()

    async def light(self) -> None:
        """Turn on the fault light"""
        self.lit = True
        await self.run_command("miner fault_light on")
        print("light " + self.ip)

    async def unlight(self) -> None:
        """Turn off the fault light"""
        self.lit = False
        await self.run_command("miner fault_light off")
        print("unlight" + self.ip)

    def add_to_output(self, message: str) -> None:
        text = message + "\n" + self.messages["text"]
        self.messages["text"] = text

    async def get_connection(self, username: str, password: str) -> asyncssh.connect:
        """
        Create a new asyncssh connection
        """
        conn = await asyncssh.connect(self.ip, known_hosts=None, username=username, password=password,
                                      server_host_key_algs=['ssh-rsa'])
        # return created connection
        return conn

    async def run_command(self, cmd: str) -> None:
        """Run a command on the miner"""
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()
        result = None
        # get/create ssh connection to miner
        conn = await self.get_connection("root", "admin")
        # send the command and store the result
        for i in range(3):
            try:
                result = await conn.run(cmd)
            except:
                if i == 3:
                    self.add_to_output(f"Unknown error when running the command {cmd}...")
                    return
                pass
        # let the user know the result of the command
        if result is not None:
            if result.stdout != "":
                self.add_to_output(result.stdout)
                if result.stderr != "":
                    self.add_to_output("ERROR: " + result.stderr)
            elif result.stderr != "":
                self.add_to_output("ERROR: " + result.stderr)
            else:
                self.add_to_output(cmd)

    async def get_api_data(self) -> dict:
        """Get and parse API data for the client"""
        if not self.bos.is_set():
            return self.messages
        try:
            # get all data and split it up
            all_data = await self.send_api_cmd("devs+temps+fans")
            devs_raw = all_data['devs'][0]
            temps_raw = all_data['temps'][0]
            fans_raw = all_data['fans'][0]

            # parse temperature data
            temps_data = {}
            for board in range(len(temps_raw['TEMPS'])):
                temps_data[f"board_{temps_raw['TEMPS'][board]['ID']}"] = {}
                temps_data[f"board_{temps_raw['TEMPS'][board]['ID']}"]["Board"] = temps_raw['TEMPS'][board]['Board']
                temps_data[f"board_{temps_raw['TEMPS'][board]['ID']}"]["Chip"] = temps_raw['TEMPS'][board]['Chip']

            # parse individual board and chip temperature data
            for board in temps_data.keys():
                if "Board" not in temps_data[board].keys():
                    temps_data[board]["Board"] = 0
                if "Chip" not in temps_data[board].keys():
                    temps_data[board]["Chip"] = 0

            # parse hashrate data
            hr_data = {}
            for board in range(len(devs_raw['DEVS'])):
                hr_data[f"board_{devs_raw['DEVS'][board]['ID']}"] = {}
                hr_data[f"board_{devs_raw['DEVS'][board]['ID']}"]["HR"] = round(
                    devs_raw['DEVS'][board]['MHS 5s'] / 1000000,
                    2)

            # parse fan data
            fans_data = {}
            for fan in range(len(fans_raw['FANS'])):
                fans_data[f"fan_{fans_raw['FANS'][fan]['ID']}"] = {}
                fans_data[f"fan_{fans_raw['FANS'][fan]['ID']}"]['RPM'] = fans_raw['FANS'][fan]['RPM']

            # set the miner data
            miner_data = {'IP': self.ip, "Light": "show", 'Fans': fans_data, 'HR': hr_data, 'Temps': temps_data}

            # save stats for later
            self.stats = miner_data

            # return stats
            return miner_data
        except:
            # if it fails, return install data
            # usually fails on getting None from API
            self.lit = False
            data = self.messages
            data['Light'] = "show"
            return data

    async def send_dir(self, l_dir: str, r_dest: str) -> None:
        """
        Send a directory to a miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # tell the user we are sending a file to the miner
        self.add_to_output(f"Sending directory to {self.ip}...")
        # get/create ssh connection to miner
        conn = await self.get_connection("root", "admin")
        # send the file
        await asyncssh.scp(l_dir, (conn, r_dest), preserve=True, recurse=True)
        # tell the user the file was sent to the miner
        self.add_to_output(f"Directory sent...")

    async def send_file(self, l_file: str, r_dest: str) -> None:
        """
        Send a file to a miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # get/create ssh connection to miner
        conn = await self.get_connection("root", "admin")
        # send file over scp
        await asyncssh.scp(l_file, (conn, r_dest))
        self.add_to_output(f"File sent...")

    async def get_file(self, r_file: str, l_dest: str) -> None:
        """
        Copy a file from a miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # tell the user we are copying a file from the miner
        self.add_to_output(f"Copying file from {self.ip}...")
        # create ssh connection to miner
        conn = await self.get_connection("root", "admin")
        # get the file
        await asyncssh.scp((conn, r_file), l_dest)
        # tell the user we copied the file from the miner
        self.add_to_output(f"File copied...")

    async def ssh_unlock(self) -> bool:
        """
        Unlock the SSH of a miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # have to outsource this to another program
        proc = await asyncio.create_subprocess_shell(
            f'{os.path.join(os.getcwd(), "files", "asicseer_installer.exe")} -p -f {self.ip} root',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        # get stdout of the unlock
        stdout, stderr = await proc.communicate()
        # check if the webUI password needs to be reset
        print(stderr)
        if str(stdout).find("webUI") != -1:
            # tell the user to reset the webUI password
            self.add_to_output("SSH unlock failed, please reset miner with reset button...")
            # ssh unlock failed
            return False
        else:
            # tell the user the SSH unlock worked
            self.add_to_output("SSH unlock success...")
            # ssh is unlocked
            return True

    async def send_referral(self) -> None:
        """
        Send the referral IPK to a miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()
        # check if the referral file exists
        if os.path.exists(REFERRAL_FILE_S9):
            try:
                # tell the user we are sending the referral
                self.add_to_output("Sending referral IPK...")
                # create ssh connection to miner
                await self.send_file(REFERRAL_FILE_S9, '/tmp/referral.ipk')
                await self.send_file(CONFIG_FILE, '/etc/bosminer.toml')

                await self.run_command(f'opkg install /tmp/referral.ipk && /etc/init.d/bosminer restart')
                # tell the user the referral completed
                self.add_to_output(f"Referral configuration completed...")
            except OSError:
                self.add_to_output(f"Unknown error...")
        else:
            self.add_to_output("No referral file, skipping referral install")

    async def update(self) -> None:
        """
        Run the update process on the miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # tell the user we are updating
        self.add_to_output(f"Updating...")
        # create ssh connection to miner
        try:
            conn = await self.get_connection("root", "admin")
            # tell the user we are sending the update file
            self.add_to_output("Sending upgrade file...")
            # send the update file
            await self.send_file(UPDATE_FILE_S9, "/tmp/firmware.tar")
            # install the update and collect the result
            result = await conn.run(f'sysupgrade /tmp/firmware.tar')
            self.add_to_output(result.stdout.strip())
            # tell the user the update completed
            self.add_to_output(f"Update completed...")
        except OSError:
            self.add_to_output(f"Unknown error...")

    async def install(self) -> None:
        """
        Run the braiinsOS installation process on the miner
        """
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()
        # remove temp firmware directory, making sure its empty
        await self.run_command("rm -fr /tmp/firmware")
        # recreate temp firmware directory
        await self.run_command("mkdir -p /tmp/firmware")

        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()
        # ensure lib exists
        await self.run_command("mkdir -p /lib")
        # copy ld-musl-armhf.so.1 to lib
        await self.send_file(LIB_FILE_S9, "/lib/ld-musl-armhf.so.1")
        # add execute permissions to /lib/ld-musl-armhf.so.1
        await self.run_command("chmod +x /lib/ld-musl-armhf.so.1")

        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()
        # create openssh directory in /usr/lib/openssh
        await self.run_command("mkdir -p /usr/lib/openssh")
        # copy sftp-server to /usr/lib/openssh/sftp-server
        await self.send_file(SFTP_SERVER_S9, "/usr/lib/openssh/sftp-server")
        # add execute permissions to /usr/lib/openssh/sftp-server
        await self.run_command("chmod +x /usr/lib/openssh/sftp-server")

        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()
        # ensure /usr/sbin exists
        await self.run_command("mkdir -p /usr/sbin")
        # copy fw_printenv to /usr/sbin/fw_printenv
        await self.send_file(FW_PRINTENV_S9, "/usr/sbin/fw_printenv")
        # add execute permissions to /usr/sbin/fw_printenv
        await self.run_command("chmod +x /usr/sbin/fw_printenv")

        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()
        # copy over firmware files to /tmp/firmware
        await self.send_dir(FIRMWARE_PATH_S9, "/tmp")
        # add execute permissions to firmware stage 1
        await self.run_command("chmod +x /tmp/firmware/stage1.sh")

        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()
        await self.run_command("ln -fs /usr/sbin/fw_printenv /usr/sbin/fw_setenv")

        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()
        # generate random HWID to be used in install
        hwid = base64.b64encode(os.urandom(12), b'ab').decode('ascii')
        # generate install command
        install_cmd = f"cd /tmp/firmware && ls -l && /bin/sh stage1.sh \
        '{hwid}' \
        'UpstreamDataInc.test' \
        '900' \
        'yes' \
        'cond' \
        'no' \
        'no' \
        'no'"

        # run the install
        await self.run_command(f"{install_cmd} && /sbin/reboot")
        # wait 120 seconds for reboot
        self.add_to_output('Rebooting...')
        await asyncio.sleep(20)
        self.add_to_output("25% Complete...")
        await asyncio.sleep(20)
        self.add_to_output("50% Complete...")
        await asyncio.sleep(20)
        self.add_to_output("75% Complete...")
        await asyncio.sleep(20)
        self.add_to_output("Reboot Complete...")
        while not await self.ping_http():
            await asyncio.sleep(3)
        await asyncio.sleep(5)

    async def main_loop(self):
        """
        Main run loop for the testing process of the miner
        """
        # start the main loop
        while True:
            await asyncio.sleep(3)
            # check state
            if self.main_state == "start":
                # Check for http
                if await self.ping_http():
                    # check for ssh if http works
                    if await self.ping_ssh():
                        # if both ssh and http are up, the miner is on and unlocked
                        self.add_to_output('SSH Connected...')
                        # check if BraiinsOS is already on the miner
                        if (version := await self.get_version()) == "BOS+":
                            self.add_to_output('BraiinsOS+ is already installed!')
                            # set state to update BraiinsOS, skip install
                            self.main_state = "update"
                            # restart the while loop just to be safe
                            continue
                        elif version == "New":
                            self.add_to_output('BraiinsOS+ is on the newest version!')
                            # set state to complete, skip install and update
                            self.main_state = "referral"
                        else:
                            # if BraiinsOS is not installed but ssh is up, move on to installing it over ssh
                            await asyncio.sleep(5)
                            self.main_state = "install"
                    else:
                        # miner is on but has no ssh, needs to be unlocked
                        self.add_to_output('SSH Disconnected...')
                        self.add_to_output('Unlocking...')
                        # do the unlock
                        if await self.ssh_unlock():
                            # set state to install now that ssh works, ssh_unlock returns True when unlock works
                            self.main_state = "install"
                            # pause for a second to bypass bugs
                            await asyncio.sleep(5)
                            # restart the while loop just to be safe
                            continue
                        else:
                            # if ssh unlock fails, it needs to be reset, ssh_unlock will tell the user that and
                            # return false, so wait for disconnect
                            await self.wait_for_disconnect()
                            # set state to start to retry after reset
                            self.main_state = "start"
                            # restart the while loop just to be safe
                            continue
                else:
                    # if no http or ssh are present, the miner is off or not ready
                    self.add_to_output("Down...")
            # check state
            if self.main_state == "install":
                # let the user know we are starting install
                self.add_to_output('Starting install...')
                # start install
                try:
                    await self.install()
                except:
                    self.main_state = "start"
                    continue
                # after install completes, move to sending referral
                self.main_state = "referral"
            # check state
            if self.main_state == "update":
                # start update
                await self.update()
                # after update completes, move to sending referral
                await asyncio.sleep(20)
                self.main_state = "referral"
            # check state
            if self.main_state == "referral":
                await asyncio.sleep(5)
                # send the referral file, install it, and configure using config.toml
                await self.send_referral()
                # set state to done to wait for disconnect
                self.main_state = "done"
            # check state
            if self.main_state == "done":
                # wait for the user to disconnect the miner
                self.bos.set()
                await self.wait_for_disconnect()
                # set state to start and restart the process
                self.bos.clear()
                if "Light" in self.messages.keys():
                    del self.messages["Light"]
                self.main_state = "start"
                # restart main loop
                continue


class MinerList:
    def __init__(self, *items: BOSminer):
        self.miners = {}
        for item in items:
            self.miners[item.ip] = item

    def basic_data(self) -> list[dict]:
        """Give fake data to be used initializing the client side before we can get data"""
        miner_data = []
        for miner in self.miners:
            miner_data.append({'IP': miner, "text": ""})
        return miner_data

    async def pause(self, ip: str) -> None:
        """Pause a miner"""
        miner = self.miners[ip]
        await miner.pause()

    async def unpause(self, ip: str) -> None:
        """Unpause a miner"""
        miner = self.miners[ip]
        await miner.unpause()

    async def check_pause(self, ip: str) -> bool:
        """Check if a miner is paused"""
        miner = self.miners[ip]
        return not miner.running.is_set()

    async def light(self, ip: str) -> None:
        """Turn fault light on for a miner"""
        miner = self.miners[ip]
        await miner.light()

    async def unlight(self, ip: str) -> None:
        """Turn fault light off for a miner"""
        miner = self.miners[ip]
        await miner.unlight()

    async def check_light(self, ip: str) -> bool:
        """Check if fault light is on for a miner"""
        miner = self.miners[ip]
        return miner.lit

    def append(self, *items: BOSminer) -> None:
        """Add a miner to MinerList"""
        for item in items:
            self.miners[item.ip] = item

    async def get_data(self) -> list[dict]:
        """Run loop to get data from all miners"""
        tasks = [self.miners[miner].get_api_data() for miner in self.miners]
        results = await asyncio.gather(*tasks)
        return results

    async def install(self) -> None:
        """Run the install on all miners"""
        tasks = [asyncio.create_task(self.miners[miner].main_loop()) for miner in self.miners]
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    miner_ = BOSminer("172.16.1.18")
    asyncio.get_event_loop().run_until_complete(miner_.get_version())
