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
            for miner in self.miners:
                print(await miner.get_api_data())
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

        boards_data = {}
        for board in range(len(devs_raw['DEVS'])):
            boards_data[f"board_{devs_raw['DEVS'][board]['ID']}"] = {}
            boards_data[f"board_{devs_raw['DEVS'][board]['ID']}"]["HR MHS"] = devs_raw['DEVS'][board]['MHS 5s']

        for board in range(len(temps_raw['TEMPS'])):
            boards_data[f"board_{temps_raw['TEMPS'][board]['ID']}"]["Board Temp"] = temps_raw['TEMPS'][board]['Board']
            boards_data[f"board_{temps_raw['TEMPS'][board]['ID']}"]["Chip Temp"] = temps_raw['TEMPS'][board]['Chip']

        for board in boards_data.keys():
            if "Board Temp" not in boards_data[board].keys():
                boards_data[board]["Board Temp"] = 0
            if "Chip Temp" not in boards_data[board].keys():
                boards_data[board]["Chip Temp"] = 0

        fans_data = {}
        for fan in range(len(fans_raw['FANS'])):
            fans_data[f"fan_{fans_raw['FANS'][fan]['ID']}"] = {}
            fans_data[f"fan_{fans_raw['FANS'][fan]['ID']}"]['RPM'] = fans_raw['FANS'][fan]['RPM']
            fans_data[f"fan_{fans_raw['FANS'][fan]['ID']}"]['Speed'] = fans_raw['FANS'][fan]['Speed']

        miner_data = {'Time': datetime.now().strftime("%H:%M:%S.%f"),'Fans': fans_data, 'Boards': boards_data}

        self.stats = miner_data
        return miner_data


miner_list = MinerList(BOSminer("172.16.1.99"), BOSminer("172.16.1.98"))

asyncio.get_event_loop().run_until_complete(asyncio.gather(miner_list.run()))
asyncio.get_event_loop().run_forever()
