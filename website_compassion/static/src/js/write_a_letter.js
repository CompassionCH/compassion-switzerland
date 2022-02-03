//Global variables

// The images compressed
let images_comp = [];
// The list of images actually displayed inside the view
let images_list = [];
// The new non-duplicated images to add to the view
let new_images = [];

let loading = false;

// Consts
const max_size = 1000;
const hard_max_size_limit = 1e7;
const resize_limit = 2e5;

const child_id = document.getElementById("child_id");
const file_selector = document.getElementById("file_selector");
const image_display_table = document.getElementById("image_display_table");
const letter_content = document.getElementById("letter_content");
const canvas = document.createElement("canvas");

file_selector.addEventListener("change", updateImageDisplay);

const template_images = document.getElementsByClassName("template-image");
const template_id = document.getElementById("template_id");

function selectTemplate(selected_template_id) {
    // Change url to display selected template
    let search_params = new URLSearchParams(window.location.search);
    search_params.set("template_id", selected_template_id);
    let url = window.location.origin + window.location.pathname + "?" + search_params.toString();
    history.replaceState({}, document.title, url);

    // unselect all
    for(let i = 0; i < template_images.length; i++) {
        let template_image = template_images[i];
        template_image.classList.remove("border", "border-5", "border-primary");
    }

    // select the one
    let selected_template_image = document.getElementById("template-image-" + selected_template_id);
    selected_template_image.classList.add("border", "border-5", "border-primary");

    template_id.innerHTML = selected_template_id;
}

selectTemplate(template_id.innerHTML);

function load_auto_text(child_id) {
    let el = document.getElementById("auto_text_" + child_id);
    if(el) {
        letter_content.value = el.innerHTML;
    }
}
load_auto_text(new URLSearchParams(window.location.search).get("child_id"));

// add listener on child change to load the auto text
for(let i = 0; i < document.getElementsByClassName("child-card").length; i++) {
    let child_card = child_cards[i];
    child_card.addEventListener("click", function() {load_auto_text(child_card.dataset.childid)});
}

function downloadLetter() {
    window.open("/my/download/labels/?child_id=" + $('#child_id').text());
}

/**
 * This function compresses images that are too big by shrinking them and if
 * necessary compressing using JPEG
 * @param image the image to compress
 * @returns {Promise<unknown>} the image as a promised blob (to allow
 * asynchronous calls)
 */
async function compressImage(image) {
    let width = image.width;
    let height = image.height;

    // calculate the width and height, constraining the proportions
    const min_width = Math.min(width, max_size);
    const min_height = Math.min(height, max_size);
    const factor = Math.min(min_width / width, min_height / height);

    // resize the canvas and draw the image data into it
    canvas.width = Math.floor(width * factor);
    canvas.height = Math.floor(height * factor);
    let ctx = canvas.getContext("2d");
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

    return await new Promise(resolve => ctx.canvas.toBlob(resolve, "image/jpeg"));
}

/**
 * Returns the index of the file in the array object, given some of its
 * characteristics
 * @param name the name of the file
 * @param size the size of the file
 * @param type the type of the file
 * @returns {number} the index if found or -1, else
 */
Array.prototype.indexOfFile = function(name, size, type) {
    for (let i = 0; i < this.length; i++) {
        const f = this[i];
        if (f.name === name && f.size === size && f.type === type) {
            return i;
        }
    }
    return -1;
}

/**
 * Check whether a file is contained in the array object
 * @param name the name of the file
 * @param size the size of the file
 * @param type the type of the file
 * @returns {boolean} true if the file is contained in the array or false
 */
Array.prototype.containsFile = function(name, size, type) {
    return this.indexOfFile(name, size, type) !== -1;
}

/**
 * Remove the file of the array object, or does nothing if it is not contained
 * @param name the name of the file
 * @param size the size of the file
 * @param type the type of the file
 */
function removeFile(name, size, type) {
    if (images_list.containsFile(name, size, type)) {
        const index = images_list.indexOfFile(name, size, type);
        images_list.splice(index, 1);
        images_comp.splice(index, 1);
    }
}

/**
 * Remove the image from the array as well as the HTML page
 * @param name the name of the file
 * @param size the size of the file
 * @param type the type of the file
 */
function removeImage(name, size, type) {
    removeFile(name, size, type);
    document.getElementById(`${name}_${size}_${type}`).remove();
}

/**
 * Display the images contained in new_images inside the HTML page
 */
function displayImages() {

    // We use the images stored in the new_images array
    for (let i = 0; i < new_images.length; i++) {
        const original_image = new_images[i];

        if (original_image.size > hard_max_size_limit) {
            displayAlert("image_too_large");
            continue;
        }

        const reader = new FileReader();
        reader.onload = function(event) {
            let image = new Image();
            image.src = event.target.result;
            image.onload = function(event) {
                if (original_image.size > resize_limit || original_image.type.valueOf() != "image/jpeg") {
                    compressImage(image).then((blob) => {
                        blob.name = original_image.name;
                        blob.lastModified = Date.now();
                        blob.webkitRelativePath = "";
                        images_comp = images_comp.concat(blob);
                    })
                } else {
                    images_comp = images_comp.concat(original_image);
                }

                image_display_table.innerHTML += `
                    <div id="${original_image.name}_${original_image.size}_${original_image.type}" class="w-100">
                        <li class="embed-responsive-item p-2" style="position: relative;">
                            <span class="close close-image p-2" onclick="removeImage('${original_image.name}', ${original_image.size}, '${original_image.type}');">&times;</span>
                            <img class="text-center" src="${image.src}" alt="${original_image.name}" style="width: 100%; height: auto;"/>
                        </li>
                    </div>
                `;
            };
        }
        reader.readAsDataURL(original_image);
    }

    new_images = [];
}

/**
 * Handle the addition of new images and ignore the duplications
 * @param event the event containing the file, among other things
 */
function updateImageDisplay(event) {
    let input_images = event.target.files;

    // TODO CI-765: remove the following block to support multiple images
    for (let i = 0; i < images_list.length; i++) {
        const file = images_list[i];
        removeImage(file.name, file.size, file.type);
    }
    // TODO CI-765: end of block

    for (let i = 0; i < input_images.length; i++) {
        const file = input_images[i];

        const is_image = file.type.startsWith("image/");

        if (is_image && !images_list.containsFile(file.name, file.size, file.type)) {

            new_images = new_images.concat(file);
            images_list = images_list.concat(file);
        }
    }

    // TODO CI-765: uncomment the following block to support multiple images
    /*
    if (new_images.length > 0) {
        display_alert("letter_images_duplicated");
        return;
    }
    */
    // TODO CI-765: end of block

    displayImages();
}

/**
 * Starts and end the loading of the type elements
 * @param type the type of elements to start or stop loading
 */
function startStopLoading(type) {
    loading = !loading;
    $("button").attr('disabled', loading);
    if (loading) {
        document.getElementById(`${type}_normal`).style.display = "none";
        document.getElementById(`${type}_loading`).style.display = "";
    } else {
        document.getElementById(`${type}_loading`).style.display = "none";
        document.getElementById(`${type}_normal`).style.display = "";
    }
}

/**
 * Create a new letter object in the database
 * @param preview boolean to determine whether we want to see the preview
 * @param with_loading determines whether we want to have a loading or not
 * we can send a letter directly if the user pressed the corresponding button
 */
async function createLetter(preview = false, with_loading = true) {
    if (with_loading) {
        startStopLoading("preview");
    }

    let params = new URLSearchParams(window.location.search);

    json_data = {
        "letter-copy": letter_content.value,
        "selected-child": params.get("child_id"),
        "selected-letter-id": params.get("template_id"),
        "source": "website",
    }
    if (images_comp.length > 0) {
        json_data["file_upl"] = images_comp[0];
    }

    let form_data = new FormData();
    for (let key in json_data ) {
        form_data.append(key, json_data[key]);
    }

    let init = {
        method: "POST",
        // Do not set the Content-Type, otherwise the form data can not set the multipart boundary
        //headers: {"Content-Type": "multipart/form-data"},
        body: form_data
    };
    let request = new Request(`${window.location.origin}/mobile-app-api/correspondence/get_preview`);
    let response = await fetch(request, init);
    return response.text().then(function(text) {
        if (with_loading) {
            startStopLoading("preview");
        }
        if (!response.ok) {
            displayAlert("preview_error");
            return false;
        }
        if (preview) {
            window.open(text.slice(1, -1), "_blank");
        }
        return true;
    });
}

/**
 * This function takes care of sending a letter when the corresponding button
 * is clicked
 */
async function sendLetter() {
    startStopLoading("sending");
    await createLetter(preview = false, with_loading = false);

    let params = new URLSearchParams(window.location.search);

    let json_data = {
        "TemplateID": params.get("template_id"),
        "Need": params.get("child_id"),
    };

    params.forEach(function(v, k, _) {
        json_data[k] = v;
    })

    let init = {
        method: "POST",
        headers: new Headers({"Content-Type": "application/json"}),
        body: JSON.stringify(json_data)
    };
    let request = new Request(`${window.location.origin}/mobile-app-api/correspondence/send_letter`);
    let response = await fetch(request, init);
    console.log(response);
    let answer = response.text().then(function(text) {
        if (!response.ok) {
            displayAlert("letter_error");
            return false;
        }

        // Empty images and text (to avoid duplicate)
        letter_content.value = "";
        for (let i = 0; i < images_list.length; i++) {
            let image = images_list[i];
            removeImage(image.name, image.size, image.type);
        }

        $("#letter_sent_correctly").modal('show');
        $(".christmas_action").toggleClass("d-none");
    });
    startStopLoading("sending");
}