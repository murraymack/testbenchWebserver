import socketio

sio = socketio.AsyncServer(async_mode="asgi")
app = socketio.ASGIApp(sio, static_files={
    "/": "./public/"
})


@sio.event
async def connect(sid, environ):
    print("Client", sid, "connected.")


@sio.event
async def disconnect(sid):
    print("Client", sid, "disconnected.")


@sio.event
async def pause(sid, data):
    print("Pausing", data['ip'])
    await sio.emit("paused_miner", {"ip": data['ip'], "result": "success"}, to=sid)
