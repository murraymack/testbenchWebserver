import {generate_layout} from "./create_layout.js"
import {sio} from "./sio.js"

// when miner data is sent
sio.on("miner_data", (data, cb) => {
    // generate the layout of the page
    generate_layout(JSON.parse(data));

    // quick callback to server
    cb("graph data received");
});
