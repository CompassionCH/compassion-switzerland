/**
 * This function is used to display an alert when needed
 */
let displayAlert = function(id) {
    $(`#${id}`).show("slow");
    setTimeout(
        function() {
            $(`#${id}`).hide("slow");
        }, 7000
    );
};

/**
 * This function is used to jump to the right section, smoothly and with as
 * chosen offset from the top
 */
const offset = 80;
$('#section_menu li a').click(function(event) {
    if (this.hash !== "") {
        event.preventDefault();

        const hash = this.hash;

        $('html, body').animate({
            scrollTop: $(hash).offset().top - offset
        }, 500);
    }
});


$(document).ready(function() {
    $("#my_account_invoicing #year").change(function () {
        const selected = $(this).val();
        const last_complete_year = $("#last_complete_year").val()
        if (selected > last_complete_year) {
            $("#year_incomplete").show();
        } else {
            $("#year_incomplete").hide();
        }
    });
    $("#my_account_invoicing #year").val($("#last_complete_year").val());
    $(function () {
      $('[data-toggle="tooltip"]').tooltip()
    })
});
