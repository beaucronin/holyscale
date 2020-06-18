from datetime import datetime
from typing import Dict
import random
import string
from chalice import Chalice, Response
import boto3

import stripe

app = Chalice(app_name="hs-api")

secrets = boto3.client("secretsmanager")
stripe.api_key = secrets.get_secret_value(SecretId="STRIPE_API_KEY")
webhook_secret = secrets.get_secret_value(SecretId="STRIPE_WEBHOOK_SECRET")

dynamo = boto3.resource("dynamodb")
table = dynamo.Table("HolyScale")


@app.route("/payments", methods=["POST"])
def payment_intents():
    try:
        body = app.current_request.json_body
        amount = int(body["amount"])
        if amount < 100 or amount > 1000:
            raise ValueError("Amount must be between $1 and $10")
        intent = stripe.PaymentIntent.create(amount=amount, currency="usd")
        return {"client_secret": intent.client_secret}
    except Exception as e:
        return Response(status_code=400, body={"message": str(e)})


@app.route("/coinbase-notifications", methods=["POST"])
def coinbase_notifications():
    body = app.current_request.json_body
    print(body)
    return body


@app.route("/stripe-notifications", methods=["POST"])
def stripe_notifications():
    body = app.current_request.json_body
    signature = app.current_request.headers["stripe-signature"]
    try:
        event = stripe.Webhook.construct_event(
            payload=app.current_request.body,
            sig_header=signature,
            secret=webhook_secret,
        )
        data = event["data"]
        event_type = event["type"]
        data_object = data["object"]
        if event_type == "payment_intent.succeeded":
            print("💰 Payment received!")
            merchandise = on_payment(data_object.amount)
        elif event_type == "payment_intent.payment_failed":
            print("❌ Payment failed.")
        return merchandise
    except Exception as e:
        return Response(status_code=500, body={"msg": str(e)})


def on_payment(amount: int) -> Dict:
    payment_id = generate_payment_id()
    tokens = generate_tokens(amount)
    result = register_tokens(payment_id, tokens)
    return {"payment_id": payment_id, "tokens": tokens}


def register_tokens(payment_id, tokens):
    for token in tokens:
        table.put_item(
            Item={
                "PaymentId": payment_id,
                "Token": token,
                "Registered": datetime.utcnow().isoformat(),
            }
        )


def generate_payment_id():
    return f"hspmt-{random_string(16)}"


def generate_tokens(n):
    return [f"hstkn-{random_string(20)}" for _ in range(n)]


# https://alex7kom.github.io/nano-nanoid-cc/
def random_string(length):
    letters = string.ascii_lowercase + string.digits
    return "".join(random.choice(letters) for _ in range(length))
