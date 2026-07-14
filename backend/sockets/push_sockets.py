import hashlib
from flask_socketio import emit
from firebase_admin import firestore

from backend.extensions import socketio
from backend.firebase_client import db
from backend.services.auth_service import get_authenticated_user

def register_push_sockets():
    @socketio.on('save_push_subscription')
    def handle_save_push_subscription(data):
        uname = get_authenticated_user(data)
        subscription_json = data.get('subscription')

        if not uname or not subscription_json:
            return

        try:
            endpoint = subscription_json.get('endpoint')
            if not endpoint:
                return

            user_ref = db.collection('users').document(uname)

            device_id = hashlib.sha256(endpoint.encode('utf-8')).hexdigest()

            existing_subs = (
                user_ref.collection('push_subscriptions')
                .where('endpoint', '==', endpoint)
                .stream()
            )

            for doc in existing_subs:
                if doc.id != device_id:
                    doc.reference.delete()

            user_ref.collection('push_subscriptions').document(device_id).set({
                'subscription': subscription_json,
                'endpoint': endpoint,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'last_seen': firestore.SERVER_TIMESTAMP
            }, merge=True)

            emit('push_subscription_saved', {'device_id': device_id})
            print(f"Saved push subscription device {device_id} for {uname}")

        except Exception as exc:
            print(f"Error saving push subscription for {uname}: {exc}")
            
