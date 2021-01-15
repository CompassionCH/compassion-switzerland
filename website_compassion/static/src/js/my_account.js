let displayAlert = function(id) {
    $(`#${id}`).show("slow");
    setTimeout(
        function() {
            $(`#${id}`).hide("slow");
        }, 7000
    );
};

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
