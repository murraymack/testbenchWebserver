import socketio
import json
from miner_data import MinerList, BOSminer
import uvicorn


miner_list = MinerList(BOSminer("192.168.1.11"),
                       BOSminer("192.168.1.12"),
                       BOSminer("192.168.1.13"),
                       BOSminer("192.168.1.14"),
                       BOSminer("192.168.1.15"),
                       BOSminer("192.168.1.16"),
                       BOSminer("192.168.1.17"),
                       BOSminer("192.168.1.18"))
miner_data = miner_list.basic_data()
running = True


sio = socketio.AsyncServer(async_mode="asgi")
app = socketio.ASGIApp(sio, static_files={
    "/": "./public/"
})


async def cb(data):
    """Callback to print data from client"""
    print(data)


async def send_data(data):
    """Send miner data to all clients"""
    await sio.emit('miner_data', json.dumps(data), callback=cb)


@sio.event
async def connect(sid, environ) -> None:
    """Event for connection"""
    global miner_data
    if miner_data is not None:
        data = {"miners": miner_data}
        await sio.emit('miner_data', json.dumps(data), callback=cb, to=sid)


@sio.event
async def pause(sid, ip: str) -> None:
    """Event to pause a miner"""
    await miner_list.pause(ip)


@sio.event
async def unpause(sid, ip: str) -> None:
    """Event to unpause a miner"""
    await miner_list.unpause(ip)


@sio.event
async def check_pause(sid, ip: str) -> bool:
    """Event to check if a miner is paused"""
    result = await miner_list.check_pause(ip)
    return result


@sio.event
async def light(sid, ip: str) -> None:
    """Event to turn on the fault light of a miner"""
    await miner_list.light(ip)


@sio.event
async def unlight(sid, ip: str) -> None:
    """Event to turn off the fault light of a miner"""
    await miner_list.unlight(ip)


@sio.event
async def check_light(sid, ip: str) -> bool:
    """Event to check if a fault light on a miner is on"""
    result = await miner_list.check_light(ip)
    return result


async def run() -> None:
    """Run loop for getting miner data"""
    global running
    while running:
        global miner_data
        global miner_list
        miner_data = await miner_list.get_data()
        sio.start_background_task(send_data, {"miners": miner_data})
        await sio.sleep(5)


sio.start_background_task(run)

if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, log_level="info", reload=True)
