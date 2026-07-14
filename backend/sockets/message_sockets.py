import json
import threading
import traceback
from datetime import datetime, timezone

from flask_socketio import emit
from firebase_admin import firestore

from backend.extensions import socketio
from backend.firebase_client import db
from backend.state import online_users, active_chats
from backend.services.auth_service import get_authenticated_user
from backend.services.message_service import (
    get_total_unread_count_for_user,
    get_message_ref,
    broadcast_message_refresh,
)
from backend.services.push_service import send_web_push
from backend.utils import conversation_id

def register_message_sockets():
    @socketio.on('send_message')
    def handle_send_message(data):
        sender = data['sender_username']
        receiver = data['receiver_username']
        content = data.get('content', '')
        reply_to = data.get('reply_to')
        message_type = data.get('type', 'text')
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        file_type = data.get('file_type')

        conv_id = conversation_id(sender, receiver)

        conv_ref = db.collection('conversations').document(conv_id)
        if not conv_ref.get().exists:
            conv_ref.set({'participants': [sender, receiver]})
            
        is_receiver_looking = (active_chats.get(receiver) == conv_id)
        message_read_status = True if is_receiver_looking else False
        
        message_payload = {
            'sender': sender,
            'content': content,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'read': message_read_status,
            'type': message_type
        }
        if reply_to:
            message_payload['reply_to'] = reply_to
        if file_url:
            message_payload.update({
                'file_url': file_url,
                'file_name': file_name,
                'file_type': file_type
            })

        msg_doc_ref = conv_ref.collection('messages').add(message_payload)
        new_msg_id = msg_doc_ref[1].id
        if not is_receiver_looking:
            try:
                receiver_doc = db.collection('users').document(receiver).get()
                if receiver_doc.exists:
                    receiver_data = receiver_doc.to_dict()
                    current_badge_count = get_total_unread_count_for_user(receiver)
                    payload = {
                        "title": f"New message from {sender}",
                        "body": content or "Sent an attachment",
                        "url": f"/?chat={sender}&type=contact",
                        "unread_badge": current_badge_count
                    }

                    subscriptions = (
                        receiver_doc.reference
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
                        
            except Exception as p_err:
                print(f"Failed to process push notification broadcast lookup: {p_err}")
        receiver_sid = online_users.get(receiver)
        if receiver_sid:
            emit('new_message', {
                'id': new_msg_id,
                'sender_username': sender,
                'content': content,
                'is_read': message_read_status,
                'type': message_type,
                'file_url': file_url,
                'file_name': file_name,
                'file_type': file_type,
                'reply_to': reply_to,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=receiver_sid)
            emit('force_contact_refresh', room=receiver_sid)
        emit('force_contact_refresh')
        emit('send_message_response', {'success': True, 'is_read': message_read_status})


    @socketio.on('delete_message')
    def handle_delete_message(data):
        uname = get_authenticated_user(data)
        chat_type = data.get('chat_type')
        chat_name = data.get('chat_name')
        message_id = data.get('message_id')

        if not uname or not chat_type or not chat_name or not message_id:
            emit('message_action_response', {
                'success': False,
                'message': 'Invalid request.'
            })
            return

        try:
            msg_ref = get_message_ref(chat_type, chat_name, uname, message_id)
            if not msg_ref:
                emit('message_action_response', {
                    'success': False,
                    'message': 'Invalid chat type.'
                })
                return

            msg_doc = msg_ref.get()

            if not msg_doc.exists:
                emit('message_action_response', {
                    'success': False,
                    'message': 'Message not found.'
                })
                return

            msg_data = msg_doc.to_dict()

            if msg_data.get('sender') != uname:
                emit('message_action_response', {
                    'success': False,
                    'message': 'You can only delete your own messages.'
                })
                return

            msg_ref.update({
                'type': 'deleted',
                'content': 'This message was deleted',
                'file_url': firestore.DELETE_FIELD,
                'file_name': firestore.DELETE_FIELD,
                'file_type': firestore.DELETE_FIELD,
                'deleted': True,
                'edited_at': firestore.SERVER_TIMESTAMP
            })

            broadcast_message_refresh(chat_type, chat_name, uname)

            emit('message_action_response', {
                'success': True
            })

        except Exception as exc:
            print(f'Error deleting message: {exc}')
            traceback.print_exc()
            emit('message_action_response', {
                'success': False,
                'message': 'Could not delete message.'
            })
            
    @socketio.on('edit_message')
    def handle_edit_message(data):
        uname = get_authenticated_user(data)
        chat_type = data.get('chat_type')
        chat_name = data.get('chat_name')
        message_id = data.get('message_id')
        new_content = data.get('content', '').strip()

        if not uname or not chat_type or not chat_name or not message_id or not new_content:
            emit('message_action_response', {
                'success': False,
                'message': 'Invalid request.'
            })
            return

        try:
            msg_ref = get_message_ref(chat_type, chat_name, uname, message_id)
            if not msg_ref:
                emit('message_action_response', {
                    'success': False,
                    'message': 'Invalid chat type.'
                })
                return

            msg_doc = msg_ref.get()

            if not msg_doc.exists:
                emit('message_action_response', {
                    'success': False,
                    'message': 'Message not found.'
                })
                return

            msg_data = msg_doc.to_dict()

            if msg_data.get('sender') != uname:
                emit('message_action_response', {
                    'success': False,
                    'message': 'You can only edit your own messages.'
                })
                return

            if msg_data.get('type') != 'text':
                emit('message_action_response', {
                    'success': False,
                    'message': 'Only text messages can be edited.'
                })
                return

            msg_ref.update({
                'content': new_content,
                'edited': True,
                'edited_at': firestore.SERVER_TIMESTAMP
            })

            broadcast_message_refresh(chat_type, chat_name, uname)

            emit('message_action_response', {
                'success': True
            })

        except Exception as exc:
            print(f'Error editing message: {exc}')
            traceback.print_exc()
            emit('message_action_response', {
                'success': False,
                'message': 'Could not edit message.'
            })
