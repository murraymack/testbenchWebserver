import socketio
import json
from miner_data import MinerList, BOSminer

miner_data = None

sio = socketio.AsyncServer(async_mode="asgi")
app = socketio.ASGIApp(sio, static_files={
    "/": "./public/"
})


async def cb(data):
    print(data)


async def send_data(data):
    await sio.emit('miner_data', json.dumps(data), callback=cb)

@sio.event
async def connect(sid, environ):
    global miner_data
    if miner_data is not None:
        data = {"miners": miner_data}
        await sio.emit('miner_data', json.dumps(data), callback=cb, to=sid)


async def run():
    while True:
        global miner_data
        miner_list = MinerList(BOSminer("172.16.1.98"), BOSminer("172.16.1.99"))
        miner_data = await miner_list.run()
        sio.start_background_task(send_data, {"miners": miner_data})
        await sio.sleep(5)

sio.start_background_task(run)