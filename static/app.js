document.addEventListener("DOMContentLoaded", function () {
    // PayPal Buttons
    paypal.Buttons({
        createOrder: function (data, actions) {
            // Fetch the total cart price from your server
            return fetch("/get_cart_total", {
                method: "GET",
            })
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    return actions.order.create({
                        purchase_units: [
                            {
                                amount: {
                                    value: data.total,
                                    currency_code: "USD", // Change to your currency code
                                },
                            },
                        ],
                    });
                });
        },
        onApprove: function (data, actions) {
            // Capture the transaction when the user approves the payment
            return fetch("/capture_payment", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    orderID: data.orderID,
                }),
            })
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    if (data.success) {
                        // Show a success message to the user
                        document.getElementById("result-message").innerHTML = "Payment successful!";
                    } else {
                        // Show an error message to the user
                        document.getElementById("result-message").innerHTML = "Payment failed. Please try again.";
                    }
                });
        },
    }).render("#paypal-button-container");
});