import socketio
import json
import asyncio
from miner_data import MinerList, BOSminer
from sanic import Sanic

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

app = Sanic("App")

app.static('/', "./public/index.html")
app.static('/sio_events.js', "./public/sio_events.js")
app.static('/sio.js', "./public/sio.js")
app.static('/graph_options.js', "./public/graph_options.js")
app.static('/generate_graphs.js', "./public/generate_graphs.js")
app.static('/create_layout.js', "./public/create_layout.js")

sio = socketio.AsyncServer(async_mode="sanic")
sio.attach(app)


async def cb(data):
    """Callback to print data from client"""
    print(data)


async def send_install_data(data):
    """Send install data to all clients"""
    await sio.emit('install_data', json.dumps(data), callback=cb)


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
    global miner_list
    global running
    asyncio.create_task(miner_list.install())
    while running:
        global miner_data
        miner_data = await miner_list.get_data()
        sio.start_background_task(send_data, {"miners": miner_data})
        await sio.sleep(5)


app.add_task(run)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
    # uvicorn.run("app:app", host="127.0.0.1", port=8000, log_level="info", reload=True)
