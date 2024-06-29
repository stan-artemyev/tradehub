// Updates number of available shares based on the user's selection

document.getElementById("symbolSelect").addEventListener("change", function() {
    var selectedOption = this.selectedOptions[0];
    var availableShares = selectedOption.getAttribute("data-available-shares");
    document.getElementById("available_shares").innerText = availableShares || "";
    document.getElementById("available_shares_container").hidden = false; // Make the div visible
});

// Ensure the available shares are initially set to an empty string on page load/re-load
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("available_shares").innerText = "";
});