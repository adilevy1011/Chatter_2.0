from flask import request

from backend.extensions import socketio
from backend.state import online_users, active_chats, active_groups, authenticated_sessions
from backend.services.contact_service import notify_friends_of_status_change

def register_lifecycle_sockets():
    @socketio.on('connect')
    def handle_connect():
        print('User connected:', request.sid)


    @socketio.on('disconnect')
    def handle_disconnect():
        username_to_remove = None
        for uname, sid in online_users.items():
            if sid == request.sid:
                username_to_remove = uname
                break
        if username_to_remove:
            del online_users[username_to_remove]
            active_chats.pop(username_to_remove, None)
            active_groups.pop(username_to_remove, None)
            notify_friends_of_status_change(username_to_remove)
        authenticated_sessions.pop(request.sid, None)
        print(f'User {username_to_remove} disconnected')
