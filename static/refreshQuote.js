// refreshQuote function script that creates AJAX request to server to get updated stock data
function refreshQuote(symbol) {
    const payload = JSON.stringify({ symbol: symbol });
    console.log("Sending payload:", payload);

    fetch("/quote", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: payload
    })
    .then(response => {
        console.log("Response status:", response.status);
        if (!response.ok) {
            return response.json().then(error => { 
                console.error("Response error content:", error);
                throw new Error(error.error); 
            });
        }
        return response.json();
    })
    .then(data => {
        console.log("Data received:", data); // Log the entire data object
        if (data.error) {
            console.error("Error refreshing quote:", data.error);
            return;
        }
        // Update the page content with new data        
        document.getElementById("price").textContent = data.price;
        document.getElementById("price_diff").textContent = data.price_diff;
        document.getElementById("percentage_change").textContent = `(${data.percentage_change}%)`;

        // Set color dynamically
        document.getElementById("price_diff").style.color = data.price_diff_color;
        document.getElementById("percentage_change").style.color = data.price_diff_color;

        document.getElementById("current_time").textContent = data.current_time;
        document.getElementById("market").textContent = data.market;
        document.getElementById("bid_price").textContent = data.bid_price;
        document.getElementById("bid_size").textContent = data.bid_size;
        document.getElementById("ask_price").textContent = data.ask_price;
        document.getElementById("ask_size").textContent = data.ask_size;
        document.getElementById("day_high").textContent = data.day_high;
        document.getElementById("day_low").textContent = data.day_low;
        document.getElementById("market_cap").textContent = data.market_cap;
        document.getElementById("pe").textContent = data.pe;
        document.getElementById("fifty_two_week_high").textContent = data.fifty_two_week_high;
        document.getElementById("fifty_two_week_low").textContent = data.fifty_two_week_low;
        document.getElementById("volume").textContent = data.volume;
        document.getElementById("average_volume").textContent = data.average_volume;
                
        // Log updated info
        console.log("Updated information:", {
            price: document.getElementById("price").textContent,
            price_diff: document.getElementById("price_diff").textContent,
            percent_change: document.getElementById("percentage_change").textContent,
            price_diff_color: data.price_diff_color,
            current_time: document.getElementById("current_time").textContent,
            market: document.getElementById("market").textContent,
            bid_price: document.getElementById("bid_price").textContent,
            bid_size: document.getElementById("bid_size").textContent,
            ask_price: document.getElementById("ask_price").textContent,
            ask_size: document.getElementById("ask_size").textContent,
            day_high: document.getElementById("day_high").textContent,
            day_low: document.getElementById("day_low").textContent,
            market_cap: document.getElementById("market_cap").textContent,
            pe: document.getElementById("pe").textContent,
            fifty_two_week_high: document.getElementById("fifty_two_week_high").textContent,
            fifty_two_week_low: document.getElementById("fifty_two_week_low").textContent,
            volume: document.getElementById("volume").textContent,
            average_volume: document.getElementById("average_volume").textContent            
        });
    })
    .catch(error => {
        console.error("Error refreshing quote:", error);
    });
}
