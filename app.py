import socketio
import json

sio = socketio.AsyncServer(async_mode="asgi")
app = socketio.ASGIApp(sio, static_files={
    "/": "./public/"
})


async def cb(data):
    print(data)


async def task(sid):
    await sio.sleep(3)
    await sio.emit('miner_data', json.dumps({'172.16.1.99': {'Time': '16:08:52.770851',
                                                             'Fans': {'fan_0': {'RPM': 1440, 'Speed': 4},
                                                                      'fan_1': {'RPM': 900, 'Speed': 4},
                                                                      'fan_2': {'RPM': 0, 'Speed': 4},
                                                                      'fan_3': {'RPM': 0, 'Speed': 4}},
                                                             'Boards': {
                                                                 'board_6': {'HR MHS': 1129792.59419664,
                                                                             'Board Temp': 83.1875,
                                                                             'Chip Temp': 88.875}}}})
                   , callback=cb)


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
