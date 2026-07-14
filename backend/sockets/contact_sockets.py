import traceback
from datetime import datetime, timezone

from flask_socketio import emit
from firebase_admin import firestore

from backend.extensions import socketio
from backend.firebase_client import db
from backend.state import online_users
from backend.services.auth_service import get_authenticated_user
from backend.services.contact_service import (
    get_user_groups,
    get_last_dm_timestamp,
    get_last_group_timestamp,
    get_contact_added_timestamp,
)
from backend.services.push_service import send_push_to_user
from backend.utils import serialize_timestamp, conversation_id, delete_collection

def register_contact_sockets():
    @socketio.on('get_contacts')
    def handle_get_contacts(data):
        try:
            uname = get_authenticated_user(data)
            if not uname:
                emit('contacts_response', {'items': []})
                return

            user_doc = db.collection('users').document(uname).get()
            if not user_doc.exists:
                emit('contacts_response', {'items': []})
                return

            raw_contacts = user_doc.to_dict().get('contacts', [])
            raw_groups = get_user_groups(uname)

            combined_items = []

            for contact in raw_contacts:
                ts = get_last_dm_timestamp(uname, contact)
                if ts is None:
                    ts = get_contact_added_timestamp(uname, contact)

                combined_items.append({
                    'name': contact,
                    'type': 'contact',
                    'timestamp': ts
                })

            for group_name in raw_groups:
                ts = get_last_group_timestamp(group_name)
                group_doc = db.collection('group_chats').document(group_name).get()
                group_data = group_doc.to_dict() if group_doc.exists else {}

                removed_members = group_data.get('removed_members', [])
                is_removed = uname in removed_members
                
                admins = group_data.get('admins', [])
                is_admin = uname in admins
                if ts is None:
                    if is_removed:
                        ts = group_data.get('removed_at', {}).get(uname)
                    else:
                        ts = group_data.get('member_added_at', {}).get(uname)

                combined_items.append({
                    'name': group_name,
                    'type': 'group',
                    'timestamp': ts,
                    'removed': is_removed,
                    'is_admin': is_admin
                })

            def sort_key(item):
                ts = item.get('timestamp')
                if ts is None:
                    return datetime.fromtimestamp(0, tz=timezone.utc)
                if ts.tzinfo is None:
                    return ts.replace(tzinfo=timezone.utc)
                return ts

            combined_items.sort(key=sort_key, reverse=True)

            serialized_items = []
            for item in combined_items:
                serialized_items.append({
                    'name': item['name'],
                    'type': item['type'],
                    'timestamp': serialize_timestamp(item['timestamp']),
                    'removed': item.get('removed', False),
                    'is_admin': item.get('is_admin', False)
                })

            emit('contacts_response', {'items': serialized_items})

        except Exception as exc:
            print(f'Error in get_contacts: {exc}')
            traceback.print_exc()
            emit('contacts_response', {'items': []})


    @socketio.on('get_online_contacts')
    def handle_get_online_contacts(data):
        uname = get_authenticated_user(data)
        user_doc = db.collection('users').document(uname).get()
        if not user_doc.exists:
            emit('online_contacts_response', {'contacts': []})
            return
        contacts = user_doc.to_dict().get('contacts', [])
        online = [c for c in contacts if c in online_users]
        emit('online_contacts_response', {'contacts': online})


    @socketio.on('add_contact')
    def handle_add_contact(data):
        uname = get_authenticated_user(data)
        contact_username = data['contact_username']

        if uname == contact_username:
            emit('add_contact_response', {'success': False, 'message': 'Cannot add yourself'})
            return

        user1_ref = db.collection('users').document(uname)
        user2_ref = db.collection('users').document(contact_username)
        user1_doc = user1_ref.get()
        user2_doc = user2_ref.get()

        if not user1_doc.exists or not user2_doc.exists:
            emit('add_contact_response', {'success': False, 'message': 'User not found'})
            return

        user1_data = user1_doc.to_dict()
        user2_data = user2_doc.to_dict()
        user1_contacts = user1_data.get('contacts', [])
        user2_contacts = user2_data.get('contacts', [])

        added = False
        if contact_username not in user1_contacts:
            user1_contacts.append(contact_username)
            user1_ref.update({'contacts': user1_contacts})

            user1_ref.collection('contact_metadata').document(contact_username).set({
                'created_at': firestore.SERVER_TIMESTAMP
            }, merge=True)

            added = True
        if uname not in user2_contacts:
            user2_contacts.append(uname)
            user2_ref.update({'contacts': user2_contacts})

            user2_ref.collection('contact_metadata').document(uname).set({
                'created_at': firestore.SERVER_TIMESTAMP
            }, merge=True)

            added = True

        if added:
            emit('add_contact_response', {'success': True})
            send_push_to_user(contact_username, {
                "title": "New contact",
                "body": f"{uname} added you as a contact",
                "url": f"/?chat={uname}&type=contact"
            })
            # Use our updated sorting function context when pushing contact lists out
            emit('force_contact_refresh')
            u2_sid = online_users.get(contact_username)
            if u2_sid:
                emit('force_contact_refresh', room=u2_sid)
        else:
            emit('add_contact_response', {'success': False, 'message': 'Already in contacts'})


    # ============ Direct Messages ============
