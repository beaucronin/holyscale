var updateTokenList = function() {
    sp = new URLSearchParams(window.location.search);
    intentId = sp.get("intent");
    if (intentId == null) {
        console.log("Intent Id not found in url params")
    } else {
        fetch("https://api.holyscale.cloud/payment/" + intentId)
            .then(function(result) {
                return result.json()
            })
            .then(function(data) {
                tokenList = document.getElementById("tx-token-list")
                html = ""
                data.tokens.forEach(function(item) {
                    if (item.Spent) {
                        html += '<li><span class="spent-token">' + item.Token + '</span></li>';
                    } else {
                        html += '<li><span class="unspent-token">' + item.Token + '</span></li>'
                    }
                })
                tokenList.innerHTML = html;
            })

    }
}

updateTokenList();