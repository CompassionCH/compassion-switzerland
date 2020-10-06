// This function disables the next button if there isn't 2 radios checked
// (fund/sponsor and participant) and adjusts the link for next step

const submit = document.getElementById("submit");
const radios = document.querySelectorAll('input[type="radio"]');
const a = document.getElementById("url");

function clickHandler() {
  let participantId = document.querySelector('input[name="participant"]:checked');

  // Enable or disable fund according to the choice of the participant
  if (participantId && participantId.value) {
    let products_number = document.querySelector('input[name="product_goal_' +
      participantId.value + '"]').value;
    let sponsorships_number = document.querySelector('input[name="sponsorship_goal_' +
      participantId.value + '"]').value;

    // Used for automatic selection if only one type of support is chosen
    let select_product = products_number && !sponsorships_number;
    let select_sponsorship = sponsorships_number && !products_number;

    enableOrDisableDiv("product", products_number, select_product);
    enableOrDisableDiv("sponsorship", sponsorships_number, select_sponsorship);
  }

  let donationType = document.querySelector('input[name="donation-type"]:checked');

  submit.disabled = !(donationType && donationType.value &&
    participantId && participantId.value);

  if (!submit.disabled) {
    if (donationType.value === "product") {
      a.href = `/project/${a.getAttribute("project")}/donation/form/${participantId.value}`;
      a.target = "";
    }

    if (donationType.value === "sponsorship") {
      a.href = document.querySelector('input[name="sponsorship_url_' +
        participantId.value + '"]').value;
      a.target = "_blank";
    }
  }
}

// Register on each radio change
radios.forEach((radio) => {
  radio.addEventListener("change", clickHandler);
});

// Execute on page load
clickHandler();

function enableOrDisableDiv(supportType, quantity, autoSelect) {
  const element = document.getElementById(supportType + "_card");
  if (quantity && quantity !== "0") {
    if (autoSelect) {
        element.querySelector('input[name="donation-type"').checked = true;
    }
    element.style.display = "block";
  } else {
    // We uncheck elements that are hidden
    element.querySelector('input[name="donation-type"]').checked = false;
    element.style.display = "none";
  }
  return quantity && quantity !== "0";
}
