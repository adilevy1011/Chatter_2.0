import json
import re
import threading
import traceback
from datetime import datetime, timezone

from flask import request
from flask_socketio import emit
from firebase_admin import firestore

from backend.config import DEFAULT_MESSAGE_FETCH_LIMIT
from backend.extensions import socketio
from backend.firebase_client import db
from backend.state import online_users, active_chats, active_groups
from backend.services.auth_service import get_authenticated_user
from backend.services.group_service import ensure_group_admin, mark_group_conversation_read
from backend.services.message_service import get_total_unread_count_for_user
from backend.services.push_service import send_push_to_user, send_web_push
from backend.utils import delete_collection, parse_iso_timestamp, serialize_timestamp

def register_group_sockets():
    @socketio.on('delete_group_chat')
    def handle_delete_group_chat(data):
        uname = get_authenticated_user(data)
        group_name = data.get('group_name')

        if not uname or not group_name:
            emit('delete_group_chat_response', {
                'success': False,
                'message': 'Invalid request.'
            })
            return

        try:
            group_ref = db.collection('group_chats').document(group_name)
            group_doc = group_ref.get()

            if not group_doc.exists:
                emit('delete_group_chat_response', {
                    'success': False,
                    'message': 'Group not found.'
                })
                return

            group_data = group_doc.to_dict()
            members = group_data.get('members', [])
            removed_members = group_data.get('removed_members', [])
            admins = ensure_group_admin(group_ref, group_data, uname)

            if uname not in admins:
                emit('delete_group_chat_response', {
                    'success': False,
                    'message': 'Only group admins can delete this group.'
                })
                return

            all_affected_users = list(set(members + removed_members))

            delete_collection(group_ref.collection('messages'))
            group_ref.delete()

            for member in all_affected_users:
                sid = online_users.get(member)
                if sid:
                    socketio.emit('force_contact_refresh', room=sid)
                    socketio.emit('force_group_deleted', {
                        'group_name': group_name
                    }, room=sid)

            emit('delete_group_chat_response', {
                'success': True,
                'group_name': group_name
            })

        except Exception as exc:
            print(f"Error deleting group chat: {exc}")
            traceback.print_exc()
            emit('delete_group_chat_response', {
                'success': False,
                'message': 'Could not delete group chat.'
            })

    @socketio.on('get_unread_group_messages_count')
    def handle_get_unread_group_messages_count(data):
        uname = get_authenticated_user(data)
        group_name = data['group_name']

        group_ref = db.collection('group_chats').document(group_name)
        unread_count = (
            group_ref.collection('messages')
            .where(f'read_by.{uname}', '==', False)
            .count()
            .get()
        )
        def _extract_count(result):
            try:
                if result is None:
                    return 0
                try:
                    r_all = repr(result)
                    m_all = re.search(r"value=([0-9]+(?:\\.[0-9]+)?)", r_all)
                    if m_all:
                        return int(float(m_all.group(1)))
                except Exception:
                    pass
                if hasattr(result, 'count'):
                    return int(result.count)
                if hasattr(result, 'to_dict'):
                    d = result.to_dict()
                    if 'count' in d:
                        return int(d['count'])
                    if 'aggregate_fields' in d:
                        af = d['aggregate_fields']
                        for v in af.values():
                            try:
                                return int(v)
                            except Exception:
                                if isinstance(v, dict):
                                    for key in ('integerValue', 'value'):
                                        if key in v:
                                            try:
                                                return int(v[key])
                                            except Exception:
                                                pass
                if isinstance(result, (list, tuple)) and result:
                    first = result[0]
                    if isinstance(first, (int, float, str)):
                        return int(first)
                    if hasattr(first, 'value'):
                        return int(first.value)
                    if hasattr(first, 'to_dict'):
                        d = first.to_dict()
                        for k in ('count', 'integerValue', 'value'):
                            if k in d:
                                return int(d[k])
                if not isinstance(result, (str, bytes)) and hasattr(result, '__iter__'):
                    try:
                        for first in result:
                            if isinstance(first, (list, tuple)) and first:
                                for elem in first:
                                    if isinstance(elem, (int, float, str)):
                                        return int(elem)
                                    if hasattr(elem, 'value'):
                                        try:
                                            return int(elem.value)
                                        except Exception:
                                            pass
                                    if hasattr(elem, 'to_dict'):
                                        d = elem.to_dict()
                                        for k in ('count', 'integerValue', 'value'):
                                            if k in d:
                                                return int(d[k])
                            if isinstance(first, (int, float, str)):
                                return int(first)
                            if hasattr(first, 'value'):
                                return int(first.value)
                            if hasattr(first, 'to_dict'):
                                d = first.to_dict()
                                for k in ('count', 'integerValue', 'value'):
                                    if k in d:
                                        return int(d[k])
                            break
                    except Exception:
                        pass
                if isinstance(result, dict):
                    for v in result.values():
                        if isinstance(v, (int,)):
                            return int(v)
                if hasattr(result, '__dict__'):
                    for v in result.__dict__.values():
                        if isinstance(v, int):
                            return int(v)
            except Exception:
                pass
            return 0

        count_value = _extract_count(unread_count)

        emit('get_unread_group_messages_count_response', {
            'success': True,
            'group_name': group_name,
            'count': count_value
        })

    @socketio.on('enter_group')
    def handle_enter_group(data):
        uname = get_authenticated_user(data)
        group_name = data['group_name']
        
        active_groups[uname] = group_name
        active_chats.pop(uname, None)
        
        socketio.start_background_task(mark_group_conversation_read, uname, group_name)

    @socketio.on('leave_group')
    def handle_leave_group(data):
        uname = get_authenticated_user(data)
        if uname:
            active_groups.pop(uname, None)
            print(f"User {uname} left their active group.")


    @socketio.on('create_group_chat')
    def handle_create_group_chat(data):
        creator_username = data.get('creator_username')
        group_name = data.get('group_name')
        member_usernames = data.get('member_usernames', [])

        if not group_name or not member_usernames:
            emit('create_group_chat_response', {'success': False, 'message': 'Group name and members are required'})
            return

        creator_doc = db.collection('users').document(creator_username).get()
        if not creator_doc.exists:
            emit('create_group_chat_response', {'success': False, 'message': 'Creator not found'})
            return

        creator_contacts = creator_doc.to_dict().get('contacts', [])
        all_members = [creator_username]
        for uname in member_usernames:
            if uname == creator_username:
                continue
            member_doc = db.collection('users').document(uname).get()
            if not member_doc.exists:
                emit('create_group_chat_response', {'success': False, 'message': f'User {uname} not found'})
                return
            if uname not in creator_contacts:
                emit('create_group_chat_response', {'success': False, 'message': f'{uname} is not in your contacts'})
                return
            if uname not in all_members:
                all_members.append(uname)

        group_ref = db.collection('group_chats').document(group_name)
        if group_ref.get().exists:
            emit('create_group_chat_response', {'success': False, 'message': 'A group with that name already exists'})
            return

        now = firestore.SERVER_TIMESTAMP

        member_added_at = {}
        for member in all_members:
            member_added_at[member] = now

        group_ref.set({
            'name': group_name,
            'members': all_members,
            'removed_members': [],
            'admins': [creator_username],
            'created_at': now,
            'member_added_at': member_added_at,
            'removed_at': {}
        })
        group_ref.collection('messages').add({
            'type': 'system',
            'content': f'{creator_username} created the group',
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        for member_name in all_members:
            if member_name != creator_username:
                send_push_to_user(member_name, {
                    "title": "Added to group",
                    "body": f"{creator_username} added you to {group_name}",
                    "url": f"/?chat={group_name}&type=group"
                })
            sid = online_users.get(member_name)
            if sid:
                emit('force_contact_refresh', room=sid)

        emit('create_group_chat_response', {'success': True, 'message': f"Group '{group_name}' created successfully"})


    @socketio.on('send_group_message')
    def handle_send_group_message(data):
        sender = data['sender_username']
        group_name = data['group_name']
        content = data.get('content', '')
        reply_to = data.get('reply_to')
        message_type = data.get('type', 'text')
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        file_type = data.get('file_type')

        group_ref = db.collection('group_chats').document(group_name)
        group_doc = group_ref.get()
        if not group_doc.exists:
            emit('send_group_message_response', {'success': False, 'message': 'Group not found'})
            return

        members = group_doc.to_dict().get('members', [])
        if sender not in members:
            emit('send_group_message_response', {'success': False, 'message': 'You are not a member of this group'})
            return

        read_by_map = {}
        for member in members:
            if member == sender:
                continue
            is_active_now = (active_groups.get(member) == group_name)
            read_by_map[member] = True if is_active_now else False

        message_payload = {
            'sender': sender,
            'content': content,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'read_by': read_by_map,
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

        msg_doc_ref = group_ref.collection('messages').add(message_payload)
        new_msg_id = msg_doc_ref[1].id
        for member in members:
            if member != sender:
                is_member_looking = (active_groups.get(member) == group_name)
                if not is_member_looking:
                    try:
                        member_doc = db.collection('users').document(member).get()
                        if member_doc.exists:
                            member_data = member_doc.to_dict()
                            current_badge_count = get_total_unread_count_for_user(member)   
                            payload = {
                                "title": f"{group_name}: {sender}",
                                "body": content or "Sent an attachment",
                                "url": f"/?chat={group_name}&type=group",
                                "unread_badge": current_badge_count
                                
                            }

                            subscriptions = (
                                member_doc.reference
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
                        print(f"Failed to process group push notification for member {member}: {p_err}")
        for member in members:
            if member != sender:
                sid = online_users.get(member)
                if sid:
                    emit('new_group_message', {
                        'id': new_msg_id,
                        'group_name': group_name,
                        'sender_username': sender,
                        'content': content,
                        'read_by': read_by_map,
                        'type': message_type,
                        'file_url': file_url,
                        'file_name': file_name,
                        'file_type': file_type,
                        'reply_to': reply_to,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }, room=sid)
                    emit('force_contact_refresh', room=sid)
        emit('force_contact_refresh')
        emit('send_group_message_response', {'success': True})


    @socketio.on('get_group_conversation')
    def handle_get_group_conversation(data):
        print(f'Received get_group_conversation request from sid={request.sid}: {data}')
        try:
            uname = get_authenticated_user(data)
            group_name = data.get('group_name')
            if not uname or not group_name:
                emit('get_group_conversation_response', {
                    'success': False,
                    'message': 'Authentication or request payload failed.',
                    'group_name': group_name
                })
                return

            group_ref = db.collection('group_chats').document(group_name)
            group_doc = group_ref.get()
            if not group_doc.exists:
                emit('get_group_conversation_response', {'success': False, 'message': 'Group not found', 'group_name': group_name})
                return

            group_data = group_doc.to_dict()
            members = group_data.get('members', [])
            removed_members = group_data.get('removed_members', [])

            admins = ensure_group_admin(group_ref, group_data, uname)
            if uname in removed_members:
                emit('get_group_conversation_response', {
                    'success': False,
                    'removed': True,
                    'message': 'You were removed from this group chat and no longer have access to its content.',
                    'group_name': group_name
                })
                return
            if uname not in members:
                emit('get_group_conversation_response', {'success': False, 'message': 'You are not a member of this group', 'group_name': group_name})
                return

            cursor_ts = parse_iso_timestamp(data.get('cursor_timestamp'))
            query = (
                group_ref.collection('messages')
                .order_by('timestamp', direction=firestore.Query.DESCENDING)
            )
            if cursor_ts is not None:
                query = query.start_after([cursor_ts])
            docs = list(query.limit(DEFAULT_MESSAGE_FETCH_LIMIT + 1).stream())
            has_more = len(docs) > DEFAULT_MESSAGE_FETCH_LIMIT
            if has_more:
                docs = docs[:DEFAULT_MESSAGE_FETCH_LIMIT]
            docs.reverse()
            serialized = []
            for doc in docs:
                msg_data = doc.to_dict()
                serialized.append({
                    'id': doc.id,
                    'sender_username': msg_data.get('sender'),
                    'content': msg_data.get('content'),
                    'read_by': msg_data.get('read_by', {}),
                    'type': msg_data.get('type', 'text'),
                    'file_url': msg_data.get('file_url'),
                    'file_name': msg_data.get('file_name'),
                    'file_type': msg_data.get('file_type'),
                    'timestamp': serialize_timestamp(msg_data.get('timestamp')),
                    'edited': msg_data.get('edited', False),
                    'deleted': msg_data.get('deleted', False),
                    'reply_to': msg_data.get('reply_to'),
                })
            emit('get_group_conversation_response', {'success': True, 'messages': serialized, 'group_name': group_name, 'has_more': has_more,'is_admin': uname in admins, 'admins': admins})
        except Exception as exc:
            print(f'Error in get_group_conversation: {exc}')
            emit('get_group_conversation_response', {
                'success': False,
                'message': f'An error occurred while loading the group conversation: {type(exc).__name__}: {exc}',
                'group_name': data.get('group_name')
            })
    #==================Edit/Delete===================

    @socketio.on('add_group_member')
    def handle_add_group_member(data):
        uname = get_authenticated_user(data)
        group_name = data.get('group_name')
        new_member = data.get('new_member')

        if not uname or not group_name or not new_member:
            emit('group_member_update_response', {'success': False, 'message': 'Invalid request.'})
            return

        try:
            group_ref = db.collection('group_chats').document(group_name)
            group_doc = group_ref.get()

            if not group_doc.exists:
                emit('group_member_update_response', {'success': False, 'message': 'Group not found.'})
                return

            group_data = group_doc.to_dict()
            admins = ensure_group_admin(group_ref, group_data, uname)

            if uname not in admins:
                emit('group_member_update_response', {'success': False, 'message': 'Only admins can add members.'})
                return

            user_doc = db.collection('users').document(new_member).get()
            if not user_doc.exists:
                emit('group_member_update_response', {'success': False, 'message': 'User could not be found.'})
                return

            members = group_data.get('members', [])
            removed_members = group_data.get('removed_members', [])

            if new_member not in members:
                members.append(new_member)

            if new_member in removed_members:
                removed_members.remove(new_member)

            group_ref.update({
                'members': members,
                'removed_members': removed_members,
                f'member_added_at.{new_member}': firestore.SERVER_TIMESTAMP,
                f'removed_at.{new_member}': firestore.DELETE_FIELD
            })

            group_ref.collection('messages').add({
                'type': 'system',
                'content': f'{new_member} was added',
                'timestamp': firestore.SERVER_TIMESTAMP
            })

            for member in members:
                sid = online_users.get(member)
                if sid:
                    socketio.emit('force_contact_refresh', room=sid)
                    socketio.emit('force_group_refresh', {'group_name': group_name}, room=sid)

            emit('group_member_update_response', {'success': True, 'message': f'{new_member} added.'})
            send_push_to_user(new_member, {
                "title": "Added to group",
                "body": f"{uname} added you to {group_name}",
                "url": f"/?chat={group_name}&type=group"
            })
        except Exception as exc:
            print(f'Error adding group member: {exc}')
            traceback.print_exc()
            emit('group_member_update_response', {'success': False, 'message': 'Could not add member.'})
            
    @socketio.on('remove_group_member')
    def handle_remove_group_member(data):
        uname = get_authenticated_user(data)
        group_name = data.get('group_name')
        member_to_remove = data.get('member_to_remove')

        if not uname or not group_name or not member_to_remove:
            emit('group_member_update_response', {'success': False, 'message': 'Invalid request.'})
            return

        try:
            group_ref = db.collection('group_chats').document(group_name)
            group_doc = group_ref.get()

            if not group_doc.exists:
                emit('group_member_update_response', {'success': False, 'message': 'Group not found.'})
                return

            group_data = group_doc.to_dict()
            admins = ensure_group_admin(group_ref, group_data, uname)

            if uname not in admins:
                emit('group_member_update_response', {'success': False, 'message': 'Only admins can remove members.'})
                return

            if member_to_remove == uname:
                emit('group_member_update_response', {'success': False, 'message': 'Admins cannot remove themselves yet.'})
                return

            members = group_data.get('members', [])
            removed_members = group_data.get('removed_members', [])

            if member_to_remove in members:
                members.remove(member_to_remove)

            if member_to_remove not in removed_members:
                removed_members.append(member_to_remove)

            group_ref.update({
                'members': members,
                'removed_members': removed_members,
                f'removed_at.{member_to_remove}': firestore.SERVER_TIMESTAMP
            })

            group_ref.collection('messages').add({
                'type': 'system',
                'content': f'{member_to_remove} was removed',
                'timestamp': firestore.SERVER_TIMESTAMP
            })

            affected = members + [member_to_remove]

            for member in affected:
                sid = online_users.get(member)
                if sid:
                    socketio.emit('force_contact_refresh', room=sid)
                    socketio.emit('force_group_refresh', {'group_name': group_name}, room=sid)

            emit('group_member_update_response', {'success': True, 'message': f'{member_to_remove} removed.'})

        except Exception as exc:
            print(f'Error removing group member: {exc}')
            traceback.print_exc()
            emit('group_member_update_response', {'success': False, 'message': 'Could not remove member.'})

    @socketio.on('delete_removed_group')
    def handle_delete_removed_group(data):
        uname = get_authenticated_user(data)
        group_name = data.get('group_name')

        if not uname or not group_name:
            emit('delete_removed_group_response', {
                'success': False,
                'message': 'Invalid request.'
            })
            return

        try:
            group_ref = db.collection('group_chats').document(group_name)
            group_doc = group_ref.get()

            if not group_doc.exists:
                emit('delete_removed_group_response', {
                    'success': True,
                    'group_name': group_name
                })
                return

            group_data = group_doc.to_dict()
            removed_members = group_data.get('removed_members', [])

            if uname not in removed_members:
                emit('delete_removed_group_response', {
                    'success': False,
                    'message': 'You are not marked as removed from this group.'
                })
                return

            removed_members.remove(uname)

            group_ref.update({
                'removed_members': removed_members,
                f'removed_at.{uname}': firestore.DELETE_FIELD,
                f'member_added_at.{uname}': firestore.DELETE_FIELD
            })

            emit('delete_removed_group_response', {
                'success': True,
                'group_name': group_name
            })

            print(f"{uname} deleted removed group {group_name} from their list only.")

        except Exception as exc:
            print(f"Error deleting removed group for user: {exc}")
            traceback.print_exc()
            emit('delete_removed_group_response', {
                'success': False,
                'message': 'Could not delete removed group.'
            })


    @socketio.on('get_group_members')
    def handle_get_group_members(data):
        uname = get_authenticated_user(data)
        group_name = data['group_name']

        group_doc = db.collection('group_chats').document(group_name).get()
        if not group_doc.exists:
            emit('users_in_group_response', {'success': False, 'users': []})
            return

        members = group_doc.to_dict().get('members', [])
        if uname not in members:
            emit('users_in_group_response', {'success': False, 'users': []})
            return

        emit('users_in_group_response', {'success': True, 'users': members})

