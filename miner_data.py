import asyncio
import json
from datetime import datetime


class MinerList:
    def __init__(self, *items):
        self.miners = [item for item in items]

    def append(self, *items):
        for item in items:
            self.miners.append(item)

    async def run(self):
        while True:
            miner_data = []
            for miner in self.miners:
                miner_data.append(await miner.get_api_data())
            await asyncio.sleep(5)



class BOSminer:
    def __init__(self, ip):
        self.stats = None
        self.ip = ip
        self.api_port = 4028

    async def send_api_cmd(self, command):
        reader, writer = await asyncio.open_connection(self.ip, self.api_port)
        api_command = json.dumps({"command": command}).encode('utf-8')
        writer.write(api_command)
        await writer.drain()

        data = b""
        while True:
            d = await reader.read(4096)
            if not d:
                break
            data += d
        data = json.loads(data.decode('utf-8')[:-1])

        writer.close()
        await writer.wait_closed()

        return data

    async def get_api_data(self):
        all_data = await self.send_api_cmd("devs+temps+fans")
        devs_raw = all_data['devs'][0]
        temps_raw = all_data['temps'][0]
        fans_raw = all_data['fans'][0]

        temps_data = {}
        for board in range(len(temps_raw['TEMPS'])):
            temps_data[f"board_{temps_raw['TEMPS'][board]['ID']}"] = {}
            temps_data[f"board_{temps_raw['TEMPS'][board]['ID']}"]["Board"] = temps_raw['TEMPS'][board]['Board']
            temps_data[f"board_{temps_raw['TEMPS'][board]['ID']}"]["Chip"] = temps_raw['TEMPS'][board]['Chip']

        for board in temps_data.keys():
            if "Board Temp" not in temps_data[board].keys():
                temps_data[board]["Board"] = 0
            if "Chip Temp" not in temps_data[board].keys():
                temps_data[board]["Chip"] = 0

        hr_data = {}
        for board in range(len(devs_raw['DEVS'])):
            hr_data[f"board_{devs_raw['DEVS'][board]['ID']}"] = {}
            hr_data[f"board_{devs_raw['DEVS'][board]['ID']}"]["HR"] = round(devs_raw['DEVS'][board]['MHS 5s']/1000000, 2)

        fans_data = {}
        for fan in range(len(fans_raw['FANS'])):
            fans_data[f"fan_{fans_raw['FANS'][fan]['ID']}"] = {}
            fans_data[f"fan_{fans_raw['FANS'][fan]['ID']}"]['RPM'] = fans_raw['FANS'][fan]['RPM']

        miner_data = {'IP': self.ip, 'Fans': fans_data, 'HR': hr_data, 'Temps': temps_data}

        self.stats = miner_data
        return miner_data


miner_list = MinerList(BOSminer("172.16.1.99"), BOSminer("172.16.1.98"))

asyncio.get_event_loop().run_until_complete(miner_list.run())
asyncio.get_event_loop().run_forever()
