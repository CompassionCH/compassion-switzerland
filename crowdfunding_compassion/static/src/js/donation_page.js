// This function disables the next button if there isn't 2 radios checked
// (fund/sponsor and participant) and adjusts the link for next step

const submit = document.getElementById("submit");
const radios = document.querySelectorAll('input[type="radio"]');
const a = document.getElementById("url");

function clickHandler() {
  let checked_radios = document.querySelectorAll("input[type=radio]:checked").length;
  submit.disabled = checked_radios == 0 || checked_radios == 1;

  if (!submit.disabled) {
    let donationType = document.querySelector('input[name="donation-type"]:checked')
      .value;
    let participantId = document.querySelector('input[name="participant"]:checked')
      .value;

    if (donationType === "fund") {
      a.href = `/project/${a.getAttribute("project")}/donation/form/${participantId}`;
    }

    if (donationType === "sponsorship") {
        a.href = document.querySelector('input[name="sponsorship_url"]').value;
    }
  }
}

// Register on each radio change
radios.forEach((radio) => {
  radio.addEventListener("change", clickHandler);
});

// Exectute on page load
clickHandler();
