import re
import traceback

from flask import request
from flask_socketio import emit
from firebase_admin import firestore

from backend.config import DEFAULT_MESSAGE_FETCH_LIMIT
from backend.extensions import socketio
from backend.firebase_client import db
from backend.state import online_users, active_chats
from backend.services.auth_service import get_authenticated_user
from backend.services.message_service import mark_conversation_read
from backend.utils import (
    conversation_id,
    delete_collection,
    parse_iso_timestamp,
    serialize_timestamp,
)

def register_conversation_sockets():
    @socketio.on('delete_conversation')
    def handle_delete_conversation(data):
        uname = get_authenticated_user(data)
        target_name = data.get('target_name')
        target_type = data.get('target_type')

        if not uname or not target_name or not target_type:
            emit('delete_conversation_response', {
                'success': False,
                'message': 'Invalid request.'
            })
            return

        try:
            if target_type == 'contact':
                conv_id = conversation_id(uname, target_name)
                conv_ref = db.collection('conversations').document(conv_id)

                delete_collection(conv_ref.collection('messages'))
                conv_ref.delete()

                other_sid = online_users.get(target_name)
                if other_sid:
                    socketio.emit('force_contact_refresh', room=other_sid)

            elif target_type == 'group':
                group_ref = db.collection('group_chats').document(target_name)
                group_doc = group_ref.get()

                if not group_doc.exists:
                    emit('delete_conversation_response', {
                        'success': False,
                        'message': 'Group not found.'
                    })
                    return

                group_data = group_doc.to_dict()
                members = group_data.get('members', [])

                if uname not in members:
                    emit('delete_conversation_response', {
                        'success': False,
                        'message': 'You are not a member of this group.'
                    })
                    return

                delete_collection(group_ref.collection('messages'))

                group_ref.collection('messages').add({
                    'type': 'system',
                    'content': 'Conversation was cleared',
                    'timestamp': firestore.SERVER_TIMESTAMP
                })

                for member in members:
                    sid = online_users.get(member)
                    if sid:
                        socketio.emit('force_contact_refresh', room=sid)
                        socketio.emit('force_group_refresh', {
                            'group_name': target_name
                        }, room=sid)

                

            else:
                emit('delete_conversation_response', {
                    'success': False,
                    'message': 'Invalid conversation type.'
                })
                return

            emit('delete_conversation_response', {
                'success': True,
                'target_name': target_name,
                'target_type': target_type
            })

        except Exception as exc:
            print(f"Error deleting conversation: {exc}")
            traceback.print_exc()
            emit('delete_conversation_response', {
                'success': False,
                'message': 'Could not delete conversation.'
            })

    @socketio.on('get_conversation')
    def handle_get_conversation(data):
        print(f'Received get_conversation request from sid={request.sid}: {data}')
        try:
            uname = get_authenticated_user(data)
            contact_username = data.get('contact_username')
            if not uname or not contact_username:
                emit('get_conversation_response', {
                    'success': False,
                    'message': 'Authentication or request payload failed.',
                    'contact_username': contact_username
                })
                return

            conv_id = conversation_id(uname, contact_username)
            cursor_ts = parse_iso_timestamp(data.get('cursor_timestamp'))
            query = (
                db.collection('conversations')
                .document(conv_id)
                .collection('messages')
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
                    'read': msg_data.get('read'),
                    'type': msg_data.get('type', 'text'),
                    'file_url': msg_data.get('file_url'),
                    'file_name': msg_data.get('file_name'),
                    'file_type': msg_data.get('file_type'),
                    'timestamp': serialize_timestamp(msg_data.get('timestamp')),
                    'edited': msg_data.get('edited', False),
                    'deleted': msg_data.get('deleted', False),
                    'reply_to': msg_data.get('reply_to'),
                })
            emit('get_conversation_response', {'success': True, 'messages': serialized, 'contact_username': contact_username, 'has_more': has_more})
        except Exception as exc:
            tb = traceback.format_exc()
            print(f'Error in get_conversation: {exc}')
            print(tb)
            emit('get_conversation_response', {
                'success': False,
                'message': f'An error occurred while loading the conversation: {type(exc).__name__}: {exc}',
                'contact_username': data.get('contact_username'),
                'traceback': tb
            })

    @socketio.on('get_unread_messages_count')
    def handle_get_unread_messages_count(data):
        uname = get_authenticated_user(data)
        contact_username = data['contact_username']

        conv_id = conversation_id(uname, contact_username)
        unread_count = (
            db.collection('conversations')
            .document(conv_id)
            .collection('messages')
            .where('sender', '==', contact_username)
            .where('read', '==', False)
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
                                            try:
                                                r = repr(elem)
                                                m = re.search(r"value=([0-9]+(?:\\.[0-9]+)?)", r)
                                                if m:
                                                    return int(float(m.group(1)))
                                            except Exception:
                                                pass
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

        emit('get_unread_messages_count_response', {
            'success': True,
            'contact_username': contact_username,
            'count': count_value
        })

    @socketio.on('enter_chat')
    def handle_enter_chat(data):
        uname = get_authenticated_user(data)
        contact_username = data['contact_username']
        
        conv_id = conversation_id(uname, contact_username)
        active_chats[uname] = conv_id
        
        socketio.start_background_task(mark_conversation_read, uname, contact_username, conv_id)


    @socketio.on('leave_chat')
    def handle_leave_chat(data):
        uname = get_authenticated_user(data)
        if uname:
            active_chats.pop(uname, None)

