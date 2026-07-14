from datetime import datetime, timezone
from flask_socketio import emit
from firebase_admin import firestore

from backend.firebase_client import db
from backend.state import online_users
from backend.utils import conversation_id

def get_user_groups(username):
    active_query = db.collection('group_chats').where('members', 'array_contains', username).stream()
    removed_query = db.collection('group_chats').where('removed_members', 'array_contains', username).stream()

    groups = set()

    for doc in active_query:
        groups.add(doc.id)

    for doc in removed_query:
        groups.add(doc.id)

    return list(groups)

def notify_friends_of_status_change(username):
    user_doc = db.collection('users').document(username).get()
    if not user_doc.exists:
        return
    contacts = user_doc.to_dict().get('contacts', [])
    for contact_username in contacts:
        sid = online_users.get(contact_username)
        if sid:
            emit('force_contact_refresh', room=sid)


# ============ Helpers: Fetch Latest Activity Timestamps for Recency Sorting ============
def get_last_dm_timestamp(username1, username2):
    conv_id = conversation_id(username1, username2)
    last_msg_query = (
        db.collection('conversations')
        .document(conv_id)
        .collection('messages')
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )
    for doc in last_msg_query:
        ts = doc.to_dict().get('timestamp')
        if ts:
            return ts
    return None
def get_contact_created_fallback(username):
    user_doc = db.collection('users').document(username).get()
    if user_doc.exists:
        return user_doc.to_dict().get('updated_at')
    return None
    
def get_last_group_timestamp(group_name):
    group_ref = db.collection('group_chats').document(group_name)

    last_msg_query = (
        group_ref
        .collection('messages')
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

    for doc in last_msg_query:
        ts = doc.to_dict().get('timestamp')
        if ts:
            return ts

    group_doc = group_ref.get()
    if group_doc.exists:
        return group_doc.to_dict().get('created_at')

    return None
    
def get_contact_added_timestamp(username, contact_username):
    user_ref = db.collection('users').document(username)
    meta_ref = (
        user_ref
        .collection('contact_metadata')
        .document(contact_username)
    )

    meta_doc = meta_ref.get()

    if meta_doc.exists:
        return meta_doc.to_dict().get('created_at')

    fallback_time = datetime.fromtimestamp(0, tz=timezone.utc)

    meta_ref.set({
        'created_at': fallback_time,
        'auto_created': True
    }, merge=True)

    return fallback_time


