from backend.firebase_client import db
from backend.extensions import socketio
from backend.state import online_users

def ensure_group_admin(group_ref, group_data, username):
    admins = group_data.get('admins')

    if admins:
        return admins

    group_ref.update({
        'admins': [username]
    })

    return [username]
   

def mark_group_conversation_read(uname, group_name):
    group_ref = db.collection('group_chats').document(group_name)
    unread_messages = (
        group_ref.collection('messages')
        .where(f'read_by.{uname}', '==', False)
        .stream()
    )
    batch = db.batch()
    has_unread = False
    for doc in unread_messages:
        batch.update(doc.reference, {f'read_by.{uname}': True})
        has_unread = True
    if has_unread:
        batch.commit()
        group_doc = group_ref.get()
        if group_doc.exists:
            members = group_doc.to_dict().get('members', [])
            for member in members:
                if member != uname:
                    member_sid = online_users.get(member)
                    if member_sid:
                        socketio.emit('update_read_status', {'type': 'group', 'group_name': group_name}, room=member_sid)

