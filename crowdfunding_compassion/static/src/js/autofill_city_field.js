$(document).ready(function() {
    const better_zip_field = document.getElementById("partner_zip_id");
    const participant_city = document.getElementById("participant_city");

    new_options = better_zip_field.options
    var unique_zips = [];
    $.each(better_zip_field.options, function(i, el){
        if(el != null && $.inArray(el.text, unique_zips) === -1) {
            unique_zips.push(el.text);
        }
        better_zip_field.options.remove(el);
    });

    $('partner_zip_id').empty()
    for (var zip in unique_zips){
        var opt = document.createElement('option');
        opt.class = "value_item";
        opt.value = unique_zips[zip];
        opt.text = unique_zips[zip]
        opt.innerHTML = unique_zips[zip];
        better_zip_field.appendChild(opt);
    }

    better_zip_field.addEventListener("input", () => {
        participant_city.value = better_zip_field.value
    });
});


