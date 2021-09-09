import socketio
import json
from miner_data import MinerList, BOSminer

sio = socketio.AsyncServer(async_mode="asgi")
app = socketio.ASGIApp(sio, static_files={
    "/": "./public/"
})


async def cb(data):
    print(data)


async def send_data(data):
    await sio.emit('miner_data', json.dumps(data), callback=cb)


async def run():
    while True:
        miner_list = MinerList(BOSminer("172.16.1.98"), BOSminer("172.16.1.99"))
        miner_data = await miner_list.run()
        sio.start_background_task(send_data, {"miners": miner_data})
        await sio.sleep(5)

sio.start_background_task(run)