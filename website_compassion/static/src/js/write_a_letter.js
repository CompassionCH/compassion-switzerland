String.prototype.replaceRange = function(from, to, substitute) {
    var result = this.substring(0, from) + substitute;
    if (to != -1) {
        result += this.substring(to)
    }
    return result;
}

String.prototype.indexOfEnd = function(string) {
    var index = this.indexOf(string);
    return index == -1 ? -1 : index + string.length;
}

selectElement = function(obj_id, elem_type) {
    const elem_id = `${elem_type}_${obj_id}`;
    const elements = document.querySelectorAll(`img[class~="${elem_type}-image"]`);

    for (var i = 0 ; i < elements.length ; i++) {
        var element = elements[i];

        if (element.id !== elem_id) {
            element.classList.remove("border");
            element.classList.remove("border-5");
            element.classList.remove("border-primary");
            continue;
        }

        // Add border to selected child
        element.classList.add("border");
        element.classList.add("border-5");
        element.classList.add("border-primary");

        // Change url to display selected child and template id
        const base_url = window.location.origin + window.location.pathname;
        var params = window.location.search;
        const from = params.indexOfEnd(`${elem_type}_id=`);
        if (from == -1) {
            params += `&${elem_type}_id=${obj_id}`;
        } else {
            const to = params.indexOf("&", from);
            params = params.replaceRange(from, to, obj_id);
        }
        history.replaceState({}, document.title, base_url + params);

        // Scroll smoothly to selected child
        const card = document.getElementById(`card_${elem_type}_${obj_id}`);
        card.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
            inline: "start",
        });

        const name = document.getElementById(`${elem_type}_name_${obj_id}`).attributes.value.value;
        const local_id = document.getElementById(`${elem_type}_local_id_${obj_id}`);
        if (local_id) {
            document.getElementById(`${elem_type}_local_id`).attributes.value.value = local_id.attributes.value.value;
        }
        document.getElementById(`${elem_type}_id`).attributes.value.value = obj_id;
        document.getElementById(`${elem_type}_name`).attributes.value.value = name;
    }
}

const max_size = 1000;

const compressImage = async function(image) {
    var canvas = document.createElement('canvas');

    var width = image.width;
    var height = image.height;

    // calculate the width and height, constraining the proportions
    const min_width = Math.min(width, max_size);
    const min_height = Math.min(height, max_size);
    const factor = Math.min(min_width / width, min_height / height);

    // resize the canvas and draw the image data into it
    canvas.width = Math.floor(width * factor);
    canvas.height = Math.floor(height * factor);
    var ctx = canvas.getContext("2d");
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

    return await new Promise(resolve => ctx.canvas.toBlob(resolve, "image/jpeg"));
}

Array.prototype.indexOfFile = function(name, size, type) {
    for (var i = 0 ; i < this.length ; i++) {
        const f = this[i];
        if (f.name === name && f.size === size && f.type === type) {
            return i;
        }
    }
    return -1;
}

Array.prototype.containsFile = function(name, size, type) {
    return this.indexOfFile(name, size, type) !== -1;
}

const removeFile = function(name, size, type) {
    if (images_list.containsFile(name, size, type)) {
        const index = images_list.indexOfFile(name, size, type);
        images_list.splice(index, 1);
        images_comp.splice(index, 1);
    }
}

const removeImage = function(name, size, type) {
    removeFile(name, size, type);
    document.getElementById(`${name}_${size}_${type}`).remove();
}

const displayImages = function() {
    const image_display = document.getElementById("image_display_table");

    for (var i = 0 ; i < new_images.length ; i++) {
        const original_image = new_images[i];

        const reader = new FileReader();
        reader.onload = function(event) {
            var image = new Image();
            image.src = event.target.result;
            image.onload = function(event) {
                if (original_image.size > 2e5) {
                    compressImage(image).then((blob) => {
                        blob.name = original_image.name;
                        blob.lastModified = Date.now();
                        blob.webkitRelativePath = "";
                        images_comp = images_comp.concat(blob);
                    })
                } else {
                    images_comp = images_comp.concat(original_image);
                }

                image_display.innerHTML += `
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

var images_comp = [];
var images_list = [];
var new_images = [];

document.getElementById("file_selector").onchange = function(event) {
    var input_images = event.target.files;
    const old_length = images_list.length;

    // TODO CI-765: remove the following block to support multiple images
    for (var i = 0 ; i < images_list.length ; i++) {
        const file = images_list[i];
        removeImage(file.name, file.size, file.type);
    }
    // TODO CI-765: end of block

    for (var i = 0 ; i < input_images.length ; i++) {
        const file = input_images[i];
        if (!images_list.containsFile(file.name, file.size, file.type)) {

            new_images = new_images.concat(file);
            images_list = images_list.concat(file);
        }
    }

    // TODO CI-765: uncomment the following block to support multiple images
    /*
    if (old_length == images_list.length) {
        display_alert("letter_images_duplicated");
        return;
    }
    */
    // TODO CI-765: end of block

    displayImages();
}

var loading = false;

const startStopLoading = function(type) {
    loading = !loading;
    $("button").attr('disabled', loading);
    if(loading) {
        document.getElementById(`${type}_normal`).style.display = "none";
        document.getElementById(`${type}_loading`).style.display = "";
    } else {
        document.getElementById(`${type}_loading`).style.display = "none";
        document.getElementById(`${type}_normal`).style.display = "";
    }
}

const createLetter = function(preview=false, with_loading=true) {
    if (with_loading) {
        startStopLoading("preview");
    }
    var form_data = new FormData();

    form_data.append("letter-copy", document.getElementById('letter_content').value);
    form_data.append("selected-child", document.getElementById('child_local_id').attributes.value.value);
    form_data.append("selected-letter-id", document.getElementById('template_id').attributes.value.value);
    form_data.append("source", "website");
    // TODO CI-765: Handle properly multiple images
    if (images_list.length > 0) {
        form_data.append("file_upl", images_comp[0]);
    }
    // TODO CI-765: end of block

    var xhr = new XMLHttpRequest();
    var url = `${window.location.origin}/mobile-app-api/correspondence/get_preview`;
    xhr.open("POST", url);
    xhr.onreadystatechange = function () {
        if (preview && xhr.readyState === 4 && xhr.status === 200) {
            if (with_loading) {
                startStopLoading("preview");
            }
            window.open(xhr.responseText.slice(1, -1), "_blank");
        }
    };
    xhr.send(form_data);
}

const sendLetter = function(message_from) {
    startStopLoading("sending");
    createLetter(preview=false, with_loading=false);

    var json_data = JSON.parse(`{
        "TemplateID": "${document.getElementById('template_id').attributes.value.value}",
        "Need": "${document.getElementById('child_id').attributes.value.value}"
    }`);

    var xhr = new XMLHttpRequest();
    var url = `${window.location.origin}/mobile-app-api/correspondence/send_letter`;
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            startStopLoading("sending");
            displayAlert("letter_sent_correctly");
        }
    };
    xhr.send(JSON.stringify(json_data));
}
