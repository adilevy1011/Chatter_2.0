import os
import json
import threading
import traceback
from pywebpush import webpush, WebPushException

from backend.firebase_client import db
from backend.state import online_users

def send_push_to_user(username, payload):
    if username in online_users:
        return

    try:
        user_doc = db.collection('users').document(username).get()
        if not user_doc.exists:
            return

        subscriptions = (
            user_doc.reference
            .collection('push_subscriptions')
            .stream()
        )

        for sub_doc in subscriptions:
            subscription = sub_doc.to_dict().get('subscription')

            if not subscription:
                continue

            push_thread = threading.Thread(
                target=send_web_push,
                args=(subscription, json.dumps(payload))
            )
            push_thread.start()

    except Exception as exc:
        print(f"Failed to send push to {username}: {exc}")
       
def send_web_push(subscription_information, message_body):
    try:
        print(f"[PUSH] Attempting outbound broadcast routing payload: {message_body}")
        webpush(
            subscription_info=subscription_information,
            data=message_body,
            vapid_private_key=os.environ.get("VAPID_PRIVATE_KEY"),
            vapid_claims={"sub": "mailto:adilevy1011@gmail.com"}
        )
        print("[PUSH] Web Push Protocol transaction handshake completed successfully!")
    except WebPushException as ex:
        print("[PUSH ERROR] WebPush protocol rejection error occurred: ", repr(ex))
        if ex.response is not None:
            print(f"[PUSH ERROR] Middleman service response body: {ex.response.status_code} - {ex.response.text}")
    except Exception as general_ex:
        print("[PUSH ERROR] General fallback runtime failure: ", traceback.format_exc())
