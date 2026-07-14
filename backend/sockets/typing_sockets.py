from flask_socketio import emit

from backend.extensions import socketio
from backend.firebase_client import db
from backend.state import online_users
from backend.services.auth_service import get_authenticated_user

def register_typing_sockets():
    def emit_typing_status(sender, chat_type, chat_name, is_typing):
        if not sender or not chat_type or not chat_name:
            return

        event_name = 'typing_status'

        if chat_type == 'contact':
            receiver = chat_name
            receiver_sid = online_users.get(receiver)

            if receiver_sid:
                socketio.emit(event_name, {
                    'chat_type': 'contact',
                    'chat_name': sender,
                    'sender': sender,
                    'is_typing': is_typing
                }, room=receiver_sid)

        elif chat_type == 'group':
            group_ref = db.collection('group_chats').document(chat_name)
            group_doc = group_ref.get()

            if not group_doc.exists:
                return

            members = group_doc.to_dict().get('members', [])

            if sender not in members:
                return

            for member in members:
                if member == sender:
                    continue

                member_sid = online_users.get(member)

                if member_sid:
                    socketio.emit(event_name, {
                        'chat_type': 'group',
                        'chat_name': chat_name,
                        'sender': sender,
                        'is_typing': is_typing
                    }, room=member_sid)


    @socketio.on('typing_start')
    def handle_typing_start(data):
        sender = get_authenticated_user(data)
        if not sender:
            return

        emit_typing_status(
            sender,
            data.get('chat_type'),
            data.get('chat_name'),
            True
        )


    @socketio.on('typing_stop')
    def handle_typing_stop(data):
        sender = get_authenticated_user(data)
        if not sender:
            return

        emit_typing_status(
            sender,
            data.get('chat_type'),
            data.get('chat_name'),
            False
        )

