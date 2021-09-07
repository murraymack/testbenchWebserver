const sio = io();

sio.on("connect", () => {
    console.log("connected");
    sio.emit("pause", {ip : "192.168.1.11"}, (data) => {
        if (data.result == "success") {
            console.log(data.ip, "pause success")
        } else if (data.result == "failed") {
                    console.log(data.ip, "pause failed")
        } else if (data.result == "error") {
                    console.log(data.ip, "pause error")
        } else {
                    console.log(data.ip, "unknown pause error")
        };
    });
});

sio.on("disconnect", () => {
    console.log("disconnected");
});

sio.on("miner_data", (data, cb) => {
    console.log(data);
    cb("graph data received");
});
