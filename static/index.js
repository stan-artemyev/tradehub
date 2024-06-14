// Function that gets values (amount of shares and symbol) from form and pass it to /buy or /sell route
function setAction(symbol, action) {
    var form = document.getElementById('form-' + symbol);
    var shares = document.getElementById('shares-' + symbol).value;

    // Validate that amount of share is not empty and > 0
    if (!shares || shares <= 0) {
        alert("Please enter a valid number of shares.");
        return;
    }

    // Set Form action based on the action parameter (buy or sell)
    if (action === 'buy') {
        form.action = '/buy';
    } else if (action === 'sell') {
        form.action = '/sell';
    }

    form.submit();
}