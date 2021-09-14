import { options_hr, options_temp, options_fans } from "./graph_options.js";
import { sio } from "./sio.js"

function pauseMiner(ip) {
    console.log("Pause" + ip)
}

function lightMiner(ip) {
    sio.emit("light", ip)
}

export function generate_graphs(data_graph) {
    var container_all = document.getElementById('chart_container');
    container_all.innerHTML = ""
    data_graph.miners.forEach(function(miner) {


        var fan_rpm_1 = miner.Fans.fan_0.RPM;
        var fan_rpm_2 = miner.Fans.fan_1.RPM;
        var hr_canvas = document.createElement('canvas');
        var temp_canvas = document.createElement('canvas');
        var fan_1_title = document.createElement('p');
        var fan_2_title = document.createElement('p');
        fan_1_title.innerHTML += "Fan 1: " + fan_rpm_1 + " RPM";
        fan_1_title.className = "text-center"
        fan_2_title.innerHTML += "Fan 2: " + fan_rpm_2 + " RPM";
        fan_2_title.className = "text-center"
        var fan_1_canvas = document.createElement('canvas');
        var fan_2_canvas = document.createElement('canvas');
        var column = document.createElement('div');
        column.className = "col border border-dark p-3"
        var row_1 = document.createElement('div');
        row_1.className = "row"
        var row_fan_title = document.createElement('div');
        row_fan_title.className = "row"
        var row_2 = document.createElement('div');
        row_2.className = "row"
        var row_3 = document.createElement('div');
        row_3.className = "row"
        var container_pause = document.createElement('div');
        container_pause.className = "form-check form-switch d-flex justify-content-evenly"
        var pause_switch = document.createElement('input');
        pause_switch.type = "checkbox"
        pause_switch.id = "pause_" + miner.IP
        pause_switch.className = "form-check-input"
        pause_switch.addEventListener("click", function(){pauseMiner(miner.IP);}, false);
        var label_pause = document.createElement("label");
        label_pause.setAttribute("for", "pause_" + miner.IP);
        label_pause.innerHTML = "Pause";
        var container_light = document.createElement('div');
        container_light.className = "form-check form-switch d-flex justify-content-evenly"
        var light_switch = document.createElement('input');
        light_switch.type = "checkbox"
        light_switch.id = "light_" + miner.IP
        light_switch.className = "form-check-input"
        light_switch.addEventListener("click", function(){lightMiner(miner.IP);}, false);
        var label_light = document.createElement("label");
        label_light.setAttribute("for", "light_" + miner.IP);
        label_light.innerHTML = "Light";


        var container_col_hr = document.createElement('div');
        var container_col_temp = document.createElement('div');
        var container_col_title_fan_1 = document.createElement('div');
        var container_col_title_fan_2 = document.createElement('div');
        var container_col_fan_1 = document.createElement('div');
        var container_col_fan_2 = document.createElement('div');
        container_col_hr.className = "col w-50 ps-0 pe-4"
        container_col_temp.className = "col w-50 ps-0 pe-4"
        container_col_title_fan_1.className = "col"
        container_col_title_fan_2.className = "col"
        container_col_fan_1.className = "col w-50 ps-3 pe-1"
        container_col_fan_2.className = "col w-50 ps-3 pe-1"


        container_col_hr.append(hr_canvas)
        container_col_temp.append(temp_canvas)
        container_col_title_fan_1.append(fan_1_title)
        container_col_title_fan_2.append(fan_2_title)
        container_col_fan_1.append(fan_1_canvas)
        container_col_fan_2.append(fan_2_canvas)
        container_light.append(light_switch)
        container_light.append(label_light)
        container_pause.append(pause_switch)
        container_pause.append(label_pause)


        var header = document.createElement('h3');
        header.className = "text-center"
        header.innerHTML += miner.IP
        column.append(header)


        row_1.append(container_col_hr)
        row_1.append(container_col_temp)
        column.append(row_1)

        row_fan_title.append(container_col_title_fan_1)
        row_fan_title.append(container_col_title_fan_2)
        column.append(row_fan_title)

        row_2.append(container_col_fan_1)
        row_2.append(container_col_fan_2)
        column.append(row_2)

        row_3.append(container_light)
        row_3.append(container_pause)
        column.append(row_3)

        container_all.append(column);

        var hr_data = []
        for (const board_num of [6, 7, 8]) {
            if (("board_" + board_num) in miner.HR) {
                var key = "board_"+board_num
                hr_data.push({label: board_num, data: [miner.HR[key].HR], backgroundColor: []})
                if (board_num == 6) {
                    hr_data[0].backgroundColor = ["rgba(12, 58, 242, 1)"]
                } else if (board_num == 7) {
                    hr_data[0].backgroundColor = ["rgba(0, 84, 219, 1)"]
                } else if (board_num == 8) {
                    hr_data[0].backgroundColor = ["rgba(0, 139, 245, 1)"]
                }
            }
        }

        var chart_hr = new Chart(hr_canvas, {
            type: "bar",
            data: {
                labels: ["Hashrate"],
                datasets: hr_data
            },
            options: options_hr
        });


        var temps_data = []
        for (const board_num of [6, 7, 8]) {
            if (("board_" + board_num) in miner.Temps) {
                key = "board_"+board_num
                temps_data.push({label: board_num + "Chip", data: [miner.Temps[key].Chip], backgroundColor: ["rgba(6, 92, 39, 1)"]});
                temps_data.push({label: board_num + "Board", data: [miner.Temps[key].Board], backgroundColor: ["rgba(255, 15, 58, 1)"]});
            }
        }


        var chart_temp = new Chart(temp_canvas, {
            type: "bar",
            data: {
                labels: ["Temps"],
                datasets: temps_data
            },
            options: options_temp,
        });



        var fan_data_1 = [fan_rpm_1, (6000-fan_rpm_1)];

        var chart_fan_1 = new Chart(fan_1_canvas, {
            type: "doughnut",
            data: {
                labels: ["Fan 1"],
                datasets: [
                    {
                        data: fan_data_1,
                        backgroundColor: [
                            "rgba(103, 0, 221, 1)",
                            "rgba(255, 255, 255, 1)"
                        ]
                    },
                ]
            },
            options: options_fans
        });


        var fan_data_2 = [fan_rpm_2, (6000-fan_rpm_2)];
        var chart_fan_2 = new Chart(fan_2_canvas, {
            type: "doughnut",
            data: {
                labels: ["Fan 2"],
                datasets: [
                    {
                        data: fan_data_2,
                        backgroundColor: [
                            "rgba(103, 0, 221, 1)",
                            "rgba(255, 255, 255, 1)"
                        ]
                    },
                ]
            },
            options: options_fans
        });
    });
}
