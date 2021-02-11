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
 * This function finds the selected item (by searching for borders and scrolls
 * to it)
 */
window.onload = function() {
    const selected_elems = document.querySelectorAll("img[class~='border']");

    for (var i = 0 ; i < selected_elems.length ; ++i) {
        const elem = selected_elems[i];
        const card = document.getElementById(`card_${elem.id}`);
        card.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
            inline: "start",
        });
    }
}

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
