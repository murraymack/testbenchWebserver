import {generate_graphs} from "./generate_graphs.js"
import {sio} from "./sio.js"

sio.on("miner_data", (data, cb) => {
    generate_graphs(JSON.parse(data));
    cb("graph data received");
});
