import socketio

sio = socketio.AsyncServer(async_mode="asgi")
app = socketio.ASGIApp(sio, static_files={
    "/": "./public/"
})

async def cb(data):
    print(data)

async def task(sid):
    await sio.sleep(5)
    await sio.emit('graph_data', {'hashrate_bds': [2, 2.2, 1.9], 'fan_spd': [90, 90]}, callback=cb)

@sio.event
async def connect(sid, environ):
    print("Client", sid, "connected.")
    sio.start_background_task(task, sid)


@sio.event
async def disconnect(sid):
    print("Client", sid, "disconnected.")


@sio.event
async def pause(sid, data):
    print("Pausing", data['ip'])
    return {"ip": data['ip'], "result": "success"}


