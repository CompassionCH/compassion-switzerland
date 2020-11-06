scrollToSelectedChild = function() {
    const images = document.querySelectorAll("img[class~='rounded-circle']");
    const scroll = document.getElementById("my_children_div");

    // We iterate over all images to find the selected one
    for (var i = 0 ; i < images.length ; i++) {
        var image = images[i];
        if (image.classList.contains("border")) {
            // We are focused on the right child, we can break
            break;
        }

        // We are focused on another image, so we scroll till the next one
        var card = document.getElementById('card_' + image.id);
        var style = window.getComputedStyle(card);
        scroll.scrollBy(card.clientWidth +
                        parseInt(style.marginLeft) +
                        parseInt(style.marginRight), 0);
    }
}

scrollToSelectedChild();
