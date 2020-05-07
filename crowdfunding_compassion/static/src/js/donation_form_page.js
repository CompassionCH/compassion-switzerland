const amountField = document.getElementById("custom-amount-field");
const amountCard = document.getElementById("custom-amount-card");
const amountHiddenField = document.getElementById("amount");
const submit = document.querySelector('button[type="submit"]');
const radios = document.querySelectorAll('input[type="radio"]');

// Select custom amount card when its textfield is clicked
amountField.addEventListener("click", () => {
  amountCard.checked = true;
  clickHandler();
});

// Update the value of the card on textfield input
amountField.addEventListener("input", () => {
  amountCard.value = amountField.value;
});

// Set value of selected amount to hidden amount form field
submit.addEventListener("click", () => {
  amountHiddenField.value = document.querySelector(
    'input[name="amount"]:checked'
  ).value;
});

// Disable button unless an amount is selected
function clickHandler() {
  let checked_radios = document.querySelectorAll("input[type=radio]:checked").length;
  submit.disabled = checked_radios == 0;
}

// Register on each radio change
radios.forEach((radio) => {
  radio.addEventListener("click", clickHandler);
});

// Exectute on page load
clickHandler();
