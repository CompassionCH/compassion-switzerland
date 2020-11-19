let displayAlert = function(id) {
    $(`#${id}`).show("slow");
    setTimeout(
        function() {
            $(`#${id}`).hide("slow");
        }, 7000
    );
};

scrollToSelectedElements = async function() {
    const selected_elems = document.querySelectorAll("img[class~='border']");
    // TODO: Find solution to remove next line
    await new Promise(r => setTimeout(r, 2000));
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

scrollToSelectedElements();
