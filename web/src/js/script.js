// A reference to Stripe.js
var stripe;

var orderData = {
    amount: 100,
    currency: "usd"
};

var intentId;

// Disable the button until we have Stripe set up on the page
// document.querySelector(".w-button").disabled = true;

var updateFeed = function() {
    fetch("https://api.holyscale.cloud/feed", {
        method: "GET"
    }).then(function(result) {
        return result.json();
    }).then(function(data) {
        feedList = document.getElementById("feed-list");
        feedHtml = "<table>"
        data.feed.forEach(function(item, i) {
            trClass = "";
            if (i == 0) trClass = ' class="emphasis1"';
            feedHtml += "<tr " + trClass + "><td>" + item.Message +
                "</td><td>" + item.Duration +
                "</td><td>" + item.Weight + "</td></tr>";
        })
        feedHtml += "</table>"
        feedList.innerHTML = feedHtml;
    })
}

var loadPayments = function() {
    fetch("https://api.holyscale.cloud/payments", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(orderData)
        })
        .then(function(result) {
            return result.json();
        })
        .then(function(data) {
            intentId = data.intentId;
            return setupElements(data);
        })
        .then(function({ stripe, card, clientSecret }) {
            document.querySelector(".w-button").disabled = false;
            // Handle form submission.
            var form = document.getElementById("payment-form");
            form.addEventListener("submit", function(event) {
                event.preventDefault();
                // Initiate payment when the submit button is clicked
                pay(stripe, card, clientSecret);
            });
        });
}

// Set up Stripe.js and Elements to use in checkout form
var setupElements = function(data) {
    stripe = Stripe(data.publishableKey);
    var elements = stripe.elements();
    var style = {
        base: {
            color: "#32325d",
            fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
            fontSmoothing: "antialiased",
            fontSize: "16px",
            "::placeholder": {
                color: "#aab7c4"
            }
        },
        invalid: {
            color: "#fa755a",
            iconColor: "#fa755a"
        }
    };

    var card = elements.create("card", { style: style });
    card.mount("#card-element");

    return {
        stripe: stripe,
        card: card,
        clientSecret: data.clientSecret
    };
};

/*
 * Calls stripe.confirmCardPayment which creates a pop-up modal to
 * prompt the user to enter extra authentication details without leaving your page
 */
var pay = function(stripe, card, clientSecret) {
    // changeLoadingState(true);

    // Initiate the payment.
    // If authentication is required, confirmCardPayment will automatically display a modal
    stripe
        .confirmCardPayment(clientSecret, {
            payment_method: {
                card: card
            }
        })
        .then(function(result) {
            if (result.error) {
                // Show error to your customer
                showError(result.error.message);
            } else {
                // The payment has been processed!
                orderComplete(clientSecret);
            }
        });
};

document.getElementById("message-submit").onclick = function() {
    var messageText = document.getElementById("Message").value;
    var tokensText = document.getElementById("Tokens").value;
    fetch("https://api.holyscale.cloud/user-posts", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: messageText,
                tokens: tokensText
            })
        })
        .then(function() {
            updateFeed();
            document.getElementById("Message").value = "";
            document.getElementById("Tokens").value = "";
        })
}

document.getElementById("reload-feed").onclick = function() {
    updateFeed();
}
loadPayments();
updateFeed();

/* ------- Post-payment helpers ------- */

/* Shows a success / error message when the payment is complete */
var orderComplete = function(clientSecret) {
    window.location.replace("/payment?intent=" + intentId)
};

var showError = function(errorMsgText) {
    // changeLoadingState(false);
    var errorMsg = document.querySelector(".sr-field-error");
    errorMsg.textContent = errorMsgText;
    setTimeout(function() {
        errorMsg.textContent = "";
    }, 4000);
};

// Show a spinner on payment submission
var changeLoadingState = function(isLoading) {
    if (isLoading) {
        document.querySelector(".w-button").disabled = true;
        document.querySelector("#spinner").classList.remove("hidden");
        document.querySelector("#button-text").classList.add("hidden");
    } else {
        document.querySelector(".w-button").disabled = false;
        document.querySelector("#spinner").classList.add("hidden");
        document.querySelector("#button-text").classList.remove("hidden");
    }
};