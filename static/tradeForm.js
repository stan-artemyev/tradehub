// Function that sets action in a tradeForm based on the Buy/Sell button clicked and submits the form
function setAction(action) {
    var tradeForm = document.getElementById('tradeForm');

    // Modify the form action based on the action to set proper route for backend
    if (action === 'buy') {
        tradeForm.action = '/buy'; // Change the action to '/buy' for Buy button
    } else if (action === 'sell') {
        tradeForm.action = '/sell'; // Change the action to '/sell' for Sell button
    }

    // Submit the form
    tradeForm.submit();
}