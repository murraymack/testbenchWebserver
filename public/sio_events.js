import {generate_graphs} from "./generate_graphs.js"

const sio = io();

sio.on("miner_data", (data, cb) => {
    generate_graphs(JSON.parse(data));
    cb("graph data received");
});
