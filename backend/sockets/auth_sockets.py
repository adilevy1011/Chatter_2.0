import secrets
from datetime import datetime, timezone, timedelta

import bcrypt
from flask import request
from flask_socketio import emit
from firebase_admin import firestore

from backend.config import TOKEN_MAX_AGE_DAYS
from backend.extensions import socketio, limiter
from backend.firebase_client import db
from backend.state import online_users, authenticated_sessions
from backend.services.auth_service import get_authenticated_user
from backend.services.contact_service import notify_friends_of_status_change

def register_auth_sockets():
    @socketio.on('login')
    @limiter.limit("20 per hour")
    def handle_login(data):
        uname = data['username']
        password = data['password']
        user_ref = db.collection('users').document(uname)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            emit('login_failed', {'message': 'Login failed. Invalid username or password.'})
            return

        user_data = user_doc.to_dict()
        stored_password = user_data.get('password', '')

        if stored_password.startswith('$2b$'):
            valid = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        else:
            valid = (password == stored_password)
            if valid:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                user_ref.update({'password': hashed})
                print(f"Migrated password for {uname} to bcrypt")

        if valid:
            session_token = secrets.token_hex(32)
            user_ref.collection('sessions').add({
                'token': session_token,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            online_users[uname] = request.sid
            authenticated_sessions[request.sid] = uname
            emit('login_successful', {'username': uname, 'session_token': session_token,'email': user_data.get('email', '')})
        else:
            emit('login_failed', {'message': 'Login failed. Invalid username or password.'})

    TOKEN_MAX_AGE_DAYS = 30
    @socketio.on('change_password_in_app')
    def handle_change_password_in_app(data):
        uname = get_authenticated_user(data)
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not uname or not current_password or not new_password:
            emit('change_password_response', {'success': False, 'message': 'Invalid request parameters.'})
            return

        try:
            user_ref = db.collection('users').document(uname)
            user_doc = user_ref.get()

            if not user_doc.exists:
                emit('change_password_response', {'success': False, 'message': 'User profile not found.'})
                return

            user_data = user_doc.to_dict()
            stored_password = user_data.get('password', '')

            if stored_password.startswith('$2b$'):
                valid = bcrypt.checkpw(current_password.encode('utf-8'), stored_password.encode('utf-8'))
            else:
                valid = (current_password == stored_password)

            if not valid:
                emit('change_password_response', {'success': False, 'message': 'Incorrect current password.'})
                return

            hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_ref.update({
                'password': hashed_new_password
            })

            print(f"[AUTH] Successfully updated password architecture for user profile: {uname}")
            emit('change_password_response', {'success': True, 'message': 'Password updated successfully!'})

        except Exception as exc:
            print(f"[ERROR] Failed to execute inline password migration: {exc}")
            emit('change_password_response', {'success': False, 'message': 'A database error occurred.'})
            
                
    @socketio.on('token_login')
    def handle_token_login(data):
        token = data.get('token')
        if not token:
            emit('login_failed', {'message': 'No token provided'})
            return

        session_query = db.collection_group('sessions').where('token', '==', token).limit(1).stream()
        session_doc = next(iter(session_query), None)

        if not session_doc:
            emit('login_failed', {'message': 'Session expired. Please log in again.'})
            return

        session_data = session_doc.to_dict()
        created_at = session_data.get('created_at')

        if created_at:
            age = datetime.now(timezone.utc) - created_at
            if age > timedelta(days=TOKEN_MAX_AGE_DAYS):
                session_doc.reference.delete()
                emit('login_failed', {'message': 'Session expired. Please log in again.'})
                return

        uname = session_doc.reference.parent.parent.id
        user_doc = db.collection('users').document(uname).get()
        user_email = ""
        if user_doc.exists:
            user_email = user_doc.to_dict().get('email', '')
        online_users[uname] = request.sid
        authenticated_sessions[request.sid] = uname
        emit('login_successful', {'username': uname, 'session_token': token,'email':user_email})

    @socketio.on('save_recovery_email')
    def handle_save_recovery_email(data):
        uname = get_authenticated_user(data)
        email = data.get('email', '').strip()
        
        if not uname or not email:
            emit('save_recovery_email_response', {'success': False, 'message': 'Authentication or email missing.'})
            return
            
        try:
            db.collection('users').document(uname).update({'email': email})
            emit('save_recovery_email_response', {'success': True, 'message': 'Recovery email saved successfully!', 'email': email})
        except Exception as e:
            print(f"[ERROR] Failed to save recovery email for {uname}: {e}")
            emit('save_recovery_email_response', {'success': False, 'message': 'Database error occurred.'})
    @socketio.on('logout_user')
    def handle_logout_user(data):
        uname = get_authenticated_user(data)
        device_id = data.get('device_id')

        if not uname:
            return

        try:
            user_ref = db.collection('users').document(uname)

            if device_id:
                user_ref.collection('push_subscriptions').document(device_id).delete()

            sessions = user_ref.collection('sessions').stream()
            for doc in sessions:
                doc.reference.delete()

            authenticated_sessions.pop(request.sid, None)
            online_users.pop(uname, None)

            print(f"Logged out {uname}; removed device {device_id}")

        except Exception as exc:
            print(f"Error during logout cleanup for {uname}: {exc}")

    @socketio.on('user_exists')
    def handle_user_exists(data):
        uname = data['username']
        user_doc = db.collection('users').document(uname).get()
        emit('user_exists_response', {'exists': user_doc.exists})


    @socketio.on('create_user')
    @limiter.limit("5 per hour")
    def handle_create_user(data):
        uname = data['username']
        password = data['password']
        email = data.get('email', '').strip()
        
        user_ref = db.collection('users').document(uname)
        if user_ref.get().exists:
            emit('user_created', {'success': False, 'message': 'Username taken'})
            return
            
        session_token = secrets.token_hex(32)
        
        user_ref.set({
            'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'contacts': [],
            'email': email
        })
        
        user_ref.collection('sessions').add({
            'token': session_token,
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        online_users[uname] = request.sid
        authenticated_sessions[request.sid] = uname
        print(f"User {uname} created and initial device token stored.")
        emit('user_created', {'success': True, 'username': uname, 'session_token': session_token})


    # ============ Online Status ============
    @socketio.on('set_online_status')
    def handle_set_online_status(data):
        uname = get_authenticated_user(data)
        status = data['status']
        if status:
            online_users[uname] = request.sid
        else:
            online_users.pop(uname, None)
        notify_friends_of_status_change(uname)


    # ============ Contacts sorted by activity recency ============
