// This function disables the next button if there isn't 2 radios checked
// (fund/sponsor and participant) and adjusts the link for next step

const submit = document.getElementById("submit");
const radios = document.querySelectorAll('input[type="radio"]');
const a = document.getElementById("url");

var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
};

function clickHandler() {
  console.log("clickHandler");
  let page = $('#page').val();
  if(page == "1"){
    let participantId = document.querySelector('input[name="participant"]:checked');
    const a_step_02 = document.getElementById("a_step_02");
    direct_to_sponsorship = $("#direct_to_sponsorship").attr("checked")
    if (direct_to_sponsorship != "checked") {
        a_step_02.href = `/project/${a_step_02.getAttribute("project")}/donation?participant=${participantId.value}&page=2`;
        a_step_02.target = "";
    } else {
        a_step_02.href = document.querySelector('input[name="sponsorship_url_' + participantId.value + '"]').value;
        a_step_02.target = "_blank";
    }

  }else{
    let participantId = $('#participant').val();
    const a_step_01 = document.getElementById("a_step_01");
    a_step_01.href = `/project/${a_step_01.getAttribute("project")}/donation?participant=${participantId}&page=1`;
    a_step_01.target = "";
    // Enable or disable fund according to the choice of the participant
    if (participantId) {
      let products_number = document.querySelector('input[name="product_goal_' +
        participantId + '"]').value;
      let sponsorships_number = document.querySelector('input[name="sponsorship_goal_' +
        participantId + '"]').value;

      // Used for automatic selection if only one type of support is chosen
      let select_product = products_number && !sponsorships_number;
      let select_sponsorship = sponsorships_number && !products_number;

      enableOrDisableDiv("product", products_number, select_product);
      enableOrDisableDiv("sponsorship", sponsorships_number, select_sponsorship);
    }

    let donationType = document.querySelector('input[name="donation-type"]:checked');

    submit.disabled = !(donationType && donationType.value &&
      participantId);

    if (!submit.disabled) {
      if (donationType.value === "product") {
        a.href = `/project/${a.getAttribute("project")}/donation/form/${participantId}?page=3`;
        a.target = "";
      }

      if (donationType.value === "sponsorship") {
        a.href = document.querySelector('input[name="sponsorship_url_' +
          participantId + '"]').value;
        a.target = "_blank";
      }
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
  if (element && quantity && quantity !== "0") {
    if (autoSelect) {
        element.querySelector('input[name="donation-type"]').checked = true;
    }
    element.style.display = "block";
  } else if (element) {
    // We uncheck elements that are hidden
    element.querySelector('input[name="donation-type"]').checked = false;
    element.style.display = "none";
  }
  return quantity && quantity !== "0";
}
