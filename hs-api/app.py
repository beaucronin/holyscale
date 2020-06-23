import json
from datetime import datetime
import dateutil.parser
from typing import Dict, List, Union
import random
import string
from decimal import Decimal
from chalice import Chalice, Response, Rate
import boto3
from boto3.dynamodb.conditions import Attr, And

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import stripe

app = Chalice(app_name="hs-api")

secrets = boto3.client("secretsmanager")
STRIPE_API_KEYS = json.loads(
    secrets.get_secret_value(SecretId="STRIPE_API_KEYS")["SecretString"]
)
stripe.api_key = STRIPE_API_KEYS["STRIPE_SECRET_KEY"]
webhook_secret = json.loads(
    secrets.get_secret_value(SecretId="HOLYSCALE_STRIPE_WEBHOOK_SECRETS")[
        "SecretString"
    ]
)["HS_PAYMENTS_WEBHOOK_LIVE"]

dynamo = boto3.resource("dynamodb")
tokens_table = dynamo.Table("HolyScaleTokens")
posts_table = dynamo.Table("HolyScalePosts")

TOKEN_LENGTH = 20


@app.route("/feed", methods=["GET"], cors=True)
def feed():
    maybe_update_feed()
    result = posts_table.scan()
    items = [item for item in result["Items"] if "Weight" in item]
    items.sort(key=lambda x: x["Weight"], reverse=True)
    return {"feed": items}


@app.route("/user-posts", methods=["POST"], cors=True)
def user_posts():
    try:
        body = app.current_request.json_body
        logger.debug(body)
        if body:
            message = body.get("message", "")
            if len(message) == 0:
                return Response(status_code=400, body={"message": "No post text found"})

            tokens = parse_tokens(body.get("tokens", []))
            logger.debug(tokens)
            num_tokens = spend_tokens(tokens)
            logger.debug(num_tokens)
            if num_tokens == 0:
                return Response(
                    status_code=400,
                    body={
                        "message": "No valid, unspent tokens found",
                        "tokens": tokens,
                        "body": body,
                    },
                )

            duration = compute_duration(message, num_tokens)
            register_post(message, duration)

            return {"message": "Success", "post": message, "body": body}
        else:
            return Response(status_code=400, body={"message": "Request body is empty"})
    except Exception as e:
        logger.error(e)
        return Response(status_code=500, body={"message": str(e)})


def register_post(message: str, duration: float):
    posts_table.put_item(
        Item={
            "PostId": generate_post_id(),
            "Message": message,
            "Duration": Decimal(duration).quantize(Decimal(".001")),
            "Posted": datetime.utcnow().isoformat(),
        }
    )


def parse_tokens(raw_tokens: Union[str, List[str]]):
    token_strings: List[str]
    if isinstance(raw_tokens, str):
        token_strings = raw_tokens.split()
    elif isinstance(raw_tokens, List):
        token_strings = raw_tokens
    return [
        canonicalize_token(token)
        for token in token_strings
        if is_well_formed_token(token)
    ]


def spend_tokens(tokens: List[str]) -> int:
    n = 0
    for token in tokens:
        try:
            result = tokens_table.update_item(
                Key={"Token": token},
                UpdateExpression="SET Spent = :s",
                ExpressionAttributeValues={":s": datetime.utcnow().isoformat()},
                ConditionExpression=And(
                    Attr("Spent").not_exists(), Attr("Token").eq(token)
                ),
                ReturnValues="UPDATED_NEW",
            )

            # If Spent is newly updated, then that field did not exist before the update
            # and the token is newly spent; otherwise, the token had already been spent
            if "Attributes" in result:
                if "Spent" in result["Attributes"]:
                    n += 1
        except Exception as e:
            logger.debug(e)

    return n


def compute_duration(message: str, num_tokens: int) -> float:
    num_bytes = len(message.encode("utf-8"))
    return num_tokens / num_bytes


def maybe_update_feed():
    update_feed()


def update_feed():
    posts = posts_table.scan()
    items = posts["Items"]
    for item in items:
        weight = compute_weight(item["Duration"], item["Posted"])
        if weight == 0:
            posts_table.delete_item(Key={"PostId": item["PostId"]})
        else:
            posts_table.update_item(
                Key={"PostId": item["PostId"]},
                UpdateExpression="SET Weight = :w",
                ExpressionAttributeValues={
                    ":w": Decimal(weight).quantize(Decimal(".00001"))
                },
            )


def compute_weight(duration: Decimal, posted_ts: str) -> float:
    posted_dt = dateutil.parser.parse(posted_ts)
    now_dt = datetime.utcnow()
    elapsed_td = now_dt - posted_dt
    elapsed_sec = elapsed_td.total_seconds()
    if elapsed_sec > 60 * 60 * 24:
        return 0
    else:
        # (Log of the) exponential decay, for λ = duration and t = elapsed_sec
        return -1.0 * elapsed_sec / float(duration)


@app.route("/payments", methods=["POST"], cors=True)
def payment_intents():
    try:
        body = app.current_request.json_body
        amount = int(body["amount"])
        if amount < 100 or amount > 1000:
            raise ValueError("Amount must be between $1 and $10")
        intent = stripe.PaymentIntent.create(amount=amount, currency="usd")
        logger.debug(intent)
        return {
            "publishableKey": STRIPE_API_KEYS["STRIPE_PUBLISHABLE_KEY"],
            "clientSecret": intent.client_secret,
            "intentId": intent.id,
        }
    except Exception as e:
        return Response(status_code=400, body={"message": str(e)})


@app.route("/payment/{payment_id}", methods=["GET"], cors=True)
def payment_info(payment_id):
    result = tokens_table.query(
        IndexName="PaymentIndex",
        KeyConditionExpression="PaymentId = :p",
        ExpressionAttributeValues={":p": payment_id},
    )
    return {"tokens": result["Items"]}


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
        # event = stripe.Webhook.construct_event(
        #     payload=app.current_request.raw_body,
        #     sig_header=signature,
        #     secret=webhook_secret,
        # )
        event = body
        data = event["data"]
        event_type = event["type"]
        data_object = data["object"]
        logger.info(event_type)
        if event_type == "payment_intent.succeeded":
            logger.info("💰 Payment received!")
            merchandise = on_payment(data_object["id"], data_object["amount"])
            # register_tokens(merchandise)
        elif event_type == "payment_intent.payment_failed":
            logger.warn("❌ Payment failed.")
    except Exception as e:
        logger.error(e)


def on_payment(payment_id: str, amount: int) -> Dict:
    """Perform the tasks that should occur once a payment is received, namely
    creating and registering tokens

    Args:
        amount (int): The number of tokens to be created

    Returns:
        Dict: A dict containing the payment id and tokens
    """
    # payment_id = generate_payment_id()
    tokens = generate_tokens(amount)
    register_tokens(payment_id, tokens)
    return {"payment_id": payment_id, "tokens": tokens}


def register_tokens(payment_id: str, tokens: List[str]):
    """Register the given tokens as spendable.

    Args:
        payment_id (str): The payment which generated the tokens
        tokens (List[str]): The token itself
    """
    for token in tokens:
        tokens_table.put_item(
            Item={
                "PaymentId": payment_id,
                "Token": token,
                "Registered": datetime.utcnow().isoformat(),
            }
        )


def generate_intent_handle():
    return f"hsint-{random_string(20)}"


def generate_payment_id():
    return f"hspmt-{random_string(16)}"


def generate_post_id():
    return f"hspst-{random_string(16)}"


def generate_tokens(n):
    return [f"hstkn-{random_string(TOKEN_LENGTH)}" for _ in range(n)]


def canonicalize_token(token: str) -> str:
    if token.lower().startswith("hstkn-"):
        token = token[6:]
    return f"hstkn-{token.upper()}"


def is_well_formed_token(token: str) -> bool:
    if token.lower().startswith("hstkn-"):
        token = token[6:]
    elif token.lower().startswith("hs") and token[5] == "-":
        logger.debug(f"Invalid token (prefix): {token}")
        return False
    token = token.upper()
    if len(token) != TOKEN_LENGTH:
        logger.debug(f"Invalid token (length): {token}")
        return False
    for c in token:
        if c not in string.ascii_uppercase and c not in string.digits:
            logger.debug(f"Invalid token (character): {token}")
            return False
    return True


# https://alex7kom.github.io/nano-nanoid-cc/
def random_string(length):
    letters = string.ascii_uppercase + string.digits
    return "".join(random.choice(letters) for _ in range(length))
