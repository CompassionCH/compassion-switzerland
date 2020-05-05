$(document).ready(function () {
    $("[id^=product-choose-]").click(function () {
        // Show the product settings
        var button_id = this.getAttribute("id");
        var id_array = button_id.split("-");
        var product_index = id_array[id_array.length - 1];
        $("[id^=fund-settings-]").hide();
        $("#fund-settings-" + product_index).show();
        // Copy product_id to real form
        var product_id = $("#product-id-" + product_index).val();
        $("#product_id").val(product_id);
    });
    $("[id^=fund-number-]").change(function () {
        // Copy fund amount to real form
        $("#product_number_goal").val($(this).val());
    });
    $("#number-sponsorships").change(function () {
        // Copy sponsorship goal to real form
        $("#number_sponsorships_goal").val($(this).val());
    });
    $("#no-product").change(function () {
        $("#no_product").val($(this).val());
    });
    // Hide required fields legend
    $(".above-controls").hide();
});
