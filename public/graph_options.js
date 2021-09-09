export var options_hr = {
    responsive: true,
    //maintainAspectRatio: false,
    aspectRatio: .75,
    plugins: {
        legend: {
            display: false,
        }
    },
    scales: {
        y: {
            min: 0,
            suggestedMax: 6,
            grid: {
                color: function(context) {
                    if (context.tick.value == 4) {
                        return "rgba(0, 0, 0, 1)";
                    } else if (context.tick.value > 4) {
                        return "rgba(103, 221, 0, 1)";
                    } else if (context.tick.value < 4) {
                        return "rgba(221, 0, 103, 1)";
                    }
                }
            }
        }
    }
};

export var options_temp = {
    responsive: true,
    plugins: {
        legend: {
            display: false,
        }
    },
    //maintainAspectRatio: false,
    aspectRatio: .75,
};

export var options_fans = {
    aspectRatio: 1.5,
    events: [],
    responsive: true,
    plugins: {
        legend: {
            display: false,
        }
    }
};