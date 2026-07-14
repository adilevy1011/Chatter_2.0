import re
import traceback
from firebase_admin import firestore

from backend.firebase_client import db
from backend.extensions import socketio
from backend.state import online_users
from backend.utils import conversation_id

def get_total_unread_count_for_user(target_username):
    try:
        total = 0
        
        # 1. Gather all private DM unread counts where you are NOT the sender
        conversations = db.collection('conversations').where('participants', 'array_contains', target_username).stream()
        for conv in conversations:
            unread_dms = (
                conv.reference.collection('messages')
                .where('read', '==', False)
                .stream()
            )
            for msg in unread_dms:
                if msg.to_dict().get('sender') != target_username:
                    total += 1

        # 2. Gather all group chat unread counts
        groups = db.collection('group_chats').where('members', 'array_contains', target_username).stream()
        for group in groups:
            unread_query_result = (
                group.reference.collection('messages')
                .where(f'read_by.{target_username}', '==', False)
                .count()
                .get()
            )
            
            # Use a clean loop to safely extract the count from the Firestore Aggregation object
            extracted_group_count = 0
            if unread_query_result:
                try:
                    # In modern Firestore, query.count().get() returns a list of AggregationResult objects
                    # Each object has a .value property containing the integer
                    if isinstance(unread_query_result, list):
                        first_item = unread_query_result[0]
                        if hasattr(first_item, 'value'):
                            extracted_group_count = int(first_item.value)
                        elif isinstance(first_item, list) and hasattr(first_item[0], 'value'):
                            extracted_group_count = int(first_item[0].value)
                except Exception:
                    # Fallback to your working regex strategy if the object mapping fails
                    try:
                        r_all = repr(unread_query_result)
                        m_all = re.search(r"value=([0-9]+)", r_all)
                        if m_all:
                            extracted_group_count = int(m_all.group(1))
                    except Exception:
                        pass

            total += extracted_group_count

        print(f"[BADGE SYNC] Computed total background badge score for {target_username}: {total}")
        return total
    except Exception as e:
        print(f"[BADGE ERROR] Failed counting total unread items: {e}")
        traceback.print_exc()
        return 0

def mark_conversation_read(uname, contact_username, conv_id):
    conv_ref = db.collection('conversations').document(conv_id)
    unread_messages = (
        conv_ref.collection('messages')
        .where('sender', '==', contact_username)
        .where('read', '==', False)
        .stream()
    )
    batch = db.batch()
    has_unread = False
    for doc in unread_messages:
        batch.update(doc.reference, {'read': True})
        has_unread = True
    if has_unread:
        batch.commit()
        sender_sid = online_users.get(contact_username)
        if sender_sid:
            socketio.emit('update_read_status', {'type': 'private', 'chat_with': uname}, room=sender_sid)



def get_message_ref(chat_type, chat_name, sender, message_id):
    if chat_type == 'contact':
        conv_id = conversation_id(sender, chat_name)
        return (
            db.collection('conversations')
            .document(conv_id)
            .collection('messages')
            .document(message_id)
        )

    if chat_type == 'group':
        return (
            db.collection('group_chats')
            .document(chat_name)
            .collection('messages')
            .document(message_id)
        )

    return None
    

def broadcast_message_refresh(chat_type, chat_name, actor):
    if chat_type == 'contact':
        sid = online_users.get(chat_name)
        if sid:
            socketio.emit('force_conversation_refresh', {
                'type': 'contact',
                'chat_name': actor
            }, room=sid)

        actor_sid = online_users.get(actor)
        if actor_sid:
            socketio.emit('force_conversation_refresh', {
                'type': 'contact',
                'chat_name': chat_name
            }, room=actor_sid)

    elif chat_type == 'group':
        group_doc = db.collection('group_chats').document(chat_name).get()
        if not group_doc.exists:
            return

        members = group_doc.to_dict().get('members', [])

        for member in members:
            sid = online_users.get(member)
            if sid:
                socketio.emit('force_conversation_refresh', {
                    'type': 'group',
                    'chat_name': chat_name
                }, room=sid)
