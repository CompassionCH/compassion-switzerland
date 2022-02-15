let donation_ranges = document.querySelectorAll(".donation_range")
// log-scale to simplify value selection for larger amounts
let log_scale = 2
let min_value = 1
let max_value = 50

function f(x) {
    let range = max_value - min_value
    return Math.log(x) / Math.log(log_scale) * range + min_value
}

function f_inv(y) {
    let range = max_value - min_value
    return Math.exp((y - min_value) * Math.log(log_scale) / range)
}

for(let i=0; i < donation_ranges.length; i++) {
    let donation_range = donation_ranges[i]
    let donation_button = document.querySelector("#donation_button_" + donation_range.dataset.id);


    let initial_value = donation_range.value
    donation_range.min = 1
    donation_range.max = log_scale

    donation_range.get_value = function () {
        let value = this.value
        value = Math.round(f(value))
        return value
    }

    donation_range.set_value = function(value) {
        this.value = f_inv(value)
    }

    function value_changed(e) {
        let value = donation_range.get_value()
        donation_button.innerHTML = button_format.replace("%", value.toFixed(2))

        let url = new URL(donation_button, new URL(document.location.origin))
        url.searchParams.set("new_amount", value)
        donation_button.href = url.toString()
    }
    donation_range.addEventListener("input", value_changed)
    donation_range.set_value(initial_value)
    value_changed()
}