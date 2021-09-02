import socketio

sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    "/": "./public/"
})


@sio.event
def connect(sid, environ):
    print("Client", sid, "connected.")


@sio.event
def disconnect(sid):
    print("Client", sid, "disconnected.")
