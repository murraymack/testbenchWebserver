import asyncio
import json
import asyncssh


class BOSminer:
    def __init__(self, ip: str):
        self.stats = None
        self.ip = ip
        self.api_port = 4028
        self.running = asyncio.Event()
        self.running.set()
        self.lit = False
        self.conn = None

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
            # upper levels correct none to fake data
            return None

    async def pause(self) -> None:
        """Pause the miner"""
        self.running.clear()
        print("paused" + self.ip)

    async def unpause(self) -> None:
        """Unpause the miner"""
        self.running.set()
        print("unpaused" + self.ip)

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
        print(message)

    async def get_connection(self, username: str, password: str) -> asyncssh.connect:
        """
        Create a new asyncssh connection and save it
        """
        if self.conn is None:
            # if connection doesnt exist, create it
            conn = await asyncssh.connect(self.ip, known_hosts=None, username=username, password=password,
                                          server_host_key_algs=['ssh-rsa'])
            # return created connection
            self.conn = conn
        else:
            # if connection exists, return the connection
            conn = self.conn
        return conn

    async def run_command(self, cmd: str) -> None:
        """Run a command on the miner"""
        # pause logic
        if not self.running.is_set():
            self.add_to_output("Paused...")
        await self.running.wait()

        # get/create ssh connection to miner
        conn = await self.get_connection("root", "admin")
        # send the command and store the result
        try:
            result = await conn.run(cmd)
        except:
            result = await conn.run(cmd)
        # let the user know the result of the command
        if result.stdout != "":
            self.add_to_output(result.stdout)
        elif result.stderr != "":
            self.add_to_output("ERROR: " + result.stderr)
        else:
            self.add_to_output(cmd)

    async def get_api_data(self) -> dict:
        """Get and parse API data for the client"""
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
                if "Board Temp" not in temps_data[board].keys():
                    temps_data[board]["Board"] = 0
                if "Chip Temp" not in temps_data[board].keys():
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
            # if it fails, return fake data
            # usually fails on getting None from API
            return {'IP': self.ip, 'Light': 'hide', 'Fans': {"fan_0": {"RPM": 0}, "fan_1": {"RPM": 0}},
                    'HR': {"board_6": {"HR": 0}, "board_7": {"HR": 0}, "board_8": {"HR": 0}},
                    'Temps': {'board_6': {'Board': 0, 'Chip': 0}, 'board_7': {'Board': 0, 'Chip': 0},
                              'board_8': {'Board': 0, 'Chip': 0}}}


class MinerList:
    def __init__(self, *items: list[BOSminer]):
        self.miners = {}
        for item in items:
            self.miners[item.ip] = item

    def basic_data(self) -> list[dict]:
        """Give fake data to be used initializing the client side before we can get data"""
        miner_data = []
        for miner in self.miners:
            miner_data.append({'IP': miner,
                               'Light': "hide",
                               'Fans': {"fan_0": {"RPM": 0}, "fan_1": {"RPM": 0}},
                               'HR': {"board_6": {"HR": 0}, "board_7": {"HR": 0}, "board_8": {"HR": 0}},
                               'Temps': {
                                    'board_6': {'Board': 0, 'Chip': 0},
                                    'board_7': {'Board': 0, 'Chip': 0},
                                    'board_8': {'Board': 0, 'Chip': 0}}})
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

    def append(self, *items: list[BOSminer]) -> None:
        """Add a miner to MinerList"""
        for item in items:
            self.miners[item.ip] = item

    async def run(self) -> list[dict]:
        """Run loop to get data from all miners"""
        miner_data = []
        for miner in self.miners:
            miner_data.append(await self.miners[miner].get_api_data())
        return miner_data


if __name__ == '__main__':
    miner_list = MinerList(BOSminer("172.16.1.99"), BOSminer("172.16.1.98"))
    asyncio.get_event_loop().run_until_complete(miner_list.run())
    asyncio.get_event_loop().run_forever()
