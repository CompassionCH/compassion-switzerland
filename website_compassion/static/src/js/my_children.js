let child_cards = document.getElementsByClassName("child-card");
let child_images = document.getElementsByClassName("child-image");
let child_name = document.getElementsByClassName("child-name");
let child_local_id = document.getElementsByClassName("child-local_id");

function selectChild(selected_child_id, reload) {
    // Change url to display selected child
    let search_params = new URLSearchParams(window.location.search);
    search_params.set("child_id", selected_child_id);
    let url = window.location.origin + window.location.pathname + "?" + search_params.toString();
    history.replaceState({}, document.title, url);

    // on some pages, its easier to reload the page with the right url
    if(reload){
        window.location = url;
    }

    // unselect all
    for(let i = 0; i < child_cards.length; i++) {
        let child_image = child_images[i];
        child_image.classList.remove("border", "border-5", "border-primary");
        child_image.style.opacity = 0.7;

        child_name[i].style.fontWeight = "normal";
        child_local_id[i].style.fontWeight = "normal";
    }

    // select the one
    let selected_child_image = document.getElementById("child-image-" + selected_child_id);
    selected_child_image.classList.add("border", "border-5", "border-primary");
    selected_child_image.style.opacity = 1;

    document.getElementById("child-name-" + selected_child_id).style.fontWeight = "bold";
    document.getElementById("child-local_id-" + selected_child_id).style.fontWeight = "bold";

    // Scroll smoothly to selected child
    let card = document.getElementById("child-card-" + selected_child_id);
    card.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "start",
    });
}

let params = new URLSearchParams(window.location.search);
selectChild(params.get("child_id"), false);