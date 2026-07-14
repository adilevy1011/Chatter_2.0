import resend
from flask import Flask, request, Response, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta
import secrets
import bcrypt
from dotenv import load_dotenv
import os
import traceback
import threading
import json
import re
from pywebpush import webpush, WebPushException
from google.cloud import firestore_v1
from gevent.threadpool import ThreadPoolExecutor
from werkzeug.utils import secure_filename
import uuid
import hashlib
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv(os.path.expanduser("~/chatter-secrets/.env"))

cred = credentials.Certificate(os.path.expanduser("~/chatter-secrets/serviceAccountKey.json"))
firebase_admin.initialize_app(cred)
db = firestore.client()
db_async = firestore_v1.AsyncClient(project=db.project, credentials=cred.get_credential())
app = Flask(__name__, static_folder='public', static_url_path='/static')
gevent_executor = ThreadPoolExecutor(max_workers=4)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins=[
    "https://chatter-2.com",
    "https://chatter-2.duckdns.org",
    "http://147.182.235.138:5555" 
])
resend.api_key = os.environ.get("RESEND_API_KEY")
DEFAULT_MESSAGE_FETCH_LIMIT = 50

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

def serialize_timestamp(value):
    if value is None:
        return None
    try:
        return value.isoformat()
    except AttributeError:
        return str(value)


def parse_iso_timestamp(value):
    if not value:
        return None
    try:
        if isinstance(value, str):
            value = value.replace('Z', '+00:00')
            dt = datetime.fromisoformat(value)
        elif isinstance(value, datetime):
            dt = value
        else:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None
       
def send_push_to_user(username, payload):
    if username in online_users:
        return

    try:
        user_doc = db.collection('users').document(username).get()
        if not user_doc.exists:
            return

        subscriptions = (
            user_doc.reference
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

    except Exception as exc:
        print(f"Failed to send push to {username}: {exc}")
       
def send_web_push(subscription_information, message_body):
    try:
        print(f"[PUSH] Attempting outbound broadcast routing payload: {message_body}")
        webpush(
            subscription_info=subscription_information,
            data=message_body,
            vapid_private_key=os.environ.get("VAPID_PRIVATE_KEY"),
            vapid_claims={"sub": "mailto:adilevy1011@gmail.com"}
        )
        print("[PUSH] Web Push Protocol transaction handshake completed successfully!")
    except WebPushException as ex:
        print("[PUSH ERROR] WebPush protocol rejection error occurred: ", repr(ex))
        if ex.response is not None:
            print(f"[PUSH ERROR] Middleman service response body: {ex.response.status_code} - {ex.response.text}")
    except Exception as general_ex:
        print("[PUSH ERROR] General fallback runtime failure: ", traceback.format_exc())
        
@app.route('/')
def serve_index_gate():
    return send_from_directory('frontend', 'index.html')

@app.route('/auth.html')
def serve_identity_auth():
    return send_from_directory('frontend', 'auth.html')

@app.route('/chat.html')
def serve_chat_dashboard():
    return send_from_directory('frontend', 'chat.html')

@app.route('/style.css')
def style():
    return send_from_directory('frontend', 'style.css', mimetype='text/css')

@app.route('/app.js')
def app_js():
    return send_from_directory('frontend', 'app.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('frontend', 'manifest.json', mimetype='application/json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('.', 'sw.js', mimetype='application/javascript')

@app.route('/api/vapid-public-key')
def get_vapid_public_key():
    public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
    return Response(public_key, mimetype='text/plain')

@app.route('/reset-password.html')
def serve_reset_password():
    return send_from_directory('frontend', 'reset-password.html')

def send_reset_email(target_email, username, token):
    try:
        # Construct the live link pointing to your new custom domain
        reset_link = f"https://chatter-2.com/reset-password.html?token={token}"
        
        print(f"[RESEND] Sending transactional recovery routing to {target_email}")
        resend.Emails.send({
            "from": "Chatter App <security@chatter-2.com>", 
            "to": target_email,
            "subject": "Reset Your Chatter Password",
            "html": f"""
                <p>Hello {username},</p>
                <p>We received a request to reset your password for your Chatter account.</p>
                <p>Click the link below to set a new password. This link expires in 1 hour:</p>
                <p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a></p>
                <p>If you did not request this, please ignore this email.</p>
            """
        })
        return True
    except Exception as e:
        print(f"[RESEND ERROR] Failed to deliver recovery outbound envelope: {e}")
        return False

@app.route('/api/forgot-password', methods=['POST'])
@limiter.limit("3 per 15 minutes")
def handle_forgot_password_api():
    try:
        data = request.get_json() or {}
        uname = data.get('username', '').strip()
        
        if not uname:
            return jsonify({"success": False, "message": "Username is required."}), 400
            
        # 1. Look up the user document directly in Firestore
        user_ref = db.collection('users').document(uname)
        user_doc = user_ref.get()
        
        # Generic fallback response message to prevent username enumeration/scraping
        generic_success_msg = "If a matching account exists, a recovery link has been dispatched."
        
        # --- DEFENSIVE INTERCEPTION LAYER ---
        # If the user doesn't exist, exit early with a fake success.
        # This stops the code BEFORE it can ever waste token generation or Resend quota.
        if not user_doc.exists:
            return jsonify({"success": True, "message": generic_success_msg})
            
        user_data = user_doc.to_dict()
        linked_email = user_data.get('email', '').strip()
        
        # If the account exists but has no linked email, ALSO exit early with a fake success.
        # This fixes the username leakage flaw and blocks un-routable API calls.
        if not linked_email:
            return jsonify({"success": True, "message": generic_success_msg})
        # -------------------------------------
            
        # 2. Generate secure single-use recovery token metrics (Only reached by real users with emails!)
        token = secrets.token_hex(32)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # 3. Store the temporary execution intent token mapping
        db.collection('password_resets').document(token).set({
            'username': uname,
            'expires_at': expiration
        })
        
        # 4. Dispatch email to the linked address fetched strictly from the database
        email_sent = send_reset_email(linked_email, uname, token)
        
        if email_sent:
            return jsonify({"success": True, "message": generic_success_msg})
        else:
            return jsonify({"success": False, "message": "Failed to complete email transit execution lifecycle."}), 500
            
    except Exception as exc:
        print(f"[ERROR] Forgot password structural execution failure: {exc}")
        return jsonify({"success": False, "message": "Internal engine transaction failure processing request."}), 500

@app.route('/api/reset-password', methods=['POST'])
def handle_reset_password_api():
    try:
        data = request.get_json() or {}
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not token or not new_password:
            return jsonify({"success": False, "message": "Invalid token or empty password field."}), 400
            
        # 1. Fetch token record from database
        reset_ref = db.collection('password_resets').document(token)
        reset_doc = reset_ref.get()
        
        if not reset_doc.exists:
            return jsonify({"success": False, "message": "Invalid or expired authorization token."}), 400
            
        reset_data = reset_doc.to_dict()
        expires_at = reset_data.get('expires_at')
        
        # Ensure timestamp comparison forces timezone-aware evaluation
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        if datetime.now(timezone.utc) > expires_at:
            reset_ref.delete()
            return jsonify({"success": False, "message": "Authorization token has expired."}), 400
            
        uname = reset_data.get('username')
        
        # 2. Re-hash updated user passphrase structural metadata
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 3. Atomically overwrite user document credentials field and flush active open tracking sessions
        user_ref = db.collection('users').document(uname)
        user_ref.update({'password': hashed_password})
        
        # Wipe active open user tracking session sub-collections to force global login validation requirements
        sessions = user_ref.collection('sessions').stream()
        for s_doc in sessions:
            s_doc.reference.delete()
            
        # 4. Burn the temporary reset token token so it cannot be re-used
        reset_ref.delete()
        
        return jsonify({"success": True, "message": "Password updated successfully! You can now log in."})
        
    except Exception as exc:
        print(f"[ERROR] Reset password critical exception thrown: {exc}")
        return jsonify({"success": False, "message": "Internal runtime engine failure updating records."}), 500

online_users = {}
active_chats = {}
active_groups = {}
authenticated_sessions = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE

@app.route("/api/upload", methods=["POST"])
def upload_file():
    print("[UPLOAD] route hit", flush=True)

    uploaded = request.files.get("file")
    print("[UPLOAD] file received:", bool(uploaded), flush=True)

    token = request.form.get("token")
    print("[UPLOAD] token received:", bool(token), flush=True)

    if not token:
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    if not uploaded:
        return jsonify({"success": False, "message": "No file uploaded."}), 400
    print("[UPLOAD] filename:", uploaded.filename)

    original_name = secure_filename(uploaded.filename)
    ext = os.path.splitext(original_name)[1]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, stored_name)

    print("[UPLOAD] save_path:", save_path)

    try:
        uploaded.save(save_path)
        print("[UPLOAD] save complete")
    except Exception as e:
        print("[UPLOAD] save failed:", e)
        traceback.print_exc()
        return {"success": False, "message": "Could not save file."}, 500

    print("[UPLOAD] returning JSON")

    file_url = f"/uploads/{stored_name}"

    response_data = {
        "success": True,
        "file_url": file_url,
        "file_name": original_name,
        "file_type": uploaded.mimetype
    }

    print("[UPLOAD] returning JSON:", response_data)

    return jsonify(response_data)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Authentication required"}), 401

    session_query = db.collection_group('sessions').where('token', '==', token).limit(1).stream()
    session_doc = next(iter(session_query), None)

    if not session_doc:
        return jsonify({"error": "Invalid or expired session"}), 401

    session_data = session_doc.to_dict()
    created_at = session_data.get('created_at')
    if created_at:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - created_at > timedelta(days=TOKEN_MAX_AGE_DAYS):
            session_doc.reference.delete()
            return jsonify({"error": "Session expired"}), 401

    return send_from_directory(UPLOAD_FOLDER, filename)


def conversation_id(username1, username2):
    return f"{min(username1, username2)}_{max(username1, username2)}"


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


def ensure_group_admin(group_ref, group_data, username):
    admins = group_data.get('admins')

    if admins:
        return admins

    group_ref.update({
        'admins': [username]
    })

    return [username]
   
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

def get_authenticated_user(data):
    sid = request.sid
    if sid in authenticated_sessions:
        return authenticated_sessions[sid]

    token = data.get('token')
    if not token:
        return None

    session_query = db.collection_group('sessions').where('token', '==', token).limit(1).stream()
    session_doc = next(iter(session_query), None)

    if not session_doc:
        return None

    session_data = session_doc.to_dict()
    created_at = session_data.get('created_at')

    if created_at:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - created_at > timedelta(days=TOKEN_MAX_AGE_DAYS):
            session_doc.reference.delete()
            return None

    username = session_doc.reference.parent.parent.id
    authenticated_sessions[sid] = username
    return username

@socketio.on('save_push_subscription')
def handle_save_push_subscription(data):
    uname = get_authenticated_user(data)
    subscription_json = data.get('subscription')

    if not uname or not subscription_json:
        return

    try:
        endpoint = subscription_json.get('endpoint')
        if not endpoint:
            return

        user_ref = db.collection('users').document(uname)

        device_id = hashlib.sha256(endpoint.encode('utf-8')).hexdigest()

        existing_subs = (
            user_ref.collection('push_subscriptions')
            .where('endpoint', '==', endpoint)
            .stream()
        )

        for doc in existing_subs:
            if doc.id != device_id:
                doc.reference.delete()

        user_ref.collection('push_subscriptions').document(device_id).set({
            'subscription': subscription_json,
            'endpoint': endpoint,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'last_seen': firestore.SERVER_TIMESTAMP
        }, merge=True)

        emit('push_subscription_saved', {'device_id': device_id})
        print(f"Saved push subscription device {device_id} for {uname}")

    except Exception as exc:
        print(f"Error saving push subscription for {uname}: {exc}")
        
def delete_collection(collection_ref, batch_size=50):
    docs = list(collection_ref.limit(batch_size).stream())

    while docs:
        batch = db.batch()

        for doc in docs:
            batch.delete(doc.reference)

        batch.commit()

        docs = list(collection_ref.limit(batch_size).stream())

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
@socketio.on('remove_contact')
def handle_remove_contact(data):
    uname = get_authenticated_user(data)
    contact_username = data.get('contact_username')

    if not uname or not contact_username:
        emit('remove_contact_response', {
            'success': False,
            'message': 'Invalid request.'
        })
        return

    try:
        user_ref = db.collection('users').document(uname)
        contact_ref = db.collection('users').document(contact_username)

        user_doc = user_ref.get()
        contact_doc = contact_ref.get()

        if not user_doc.exists or not contact_doc.exists:
            emit('remove_contact_response', {
                'success': False,
                'message': 'User could not be found.'
            })
            return

        user_contacts = user_doc.to_dict().get('contacts', [])
        contact_contacts = contact_doc.to_dict().get('contacts', [])

        if contact_username in user_contacts:
            user_contacts.remove(contact_username)
            user_ref.update({'contacts': user_contacts})

        if uname in contact_contacts:
            contact_contacts.remove(uname)
            contact_ref.update({'contacts': contact_contacts})

        user_ref.collection('contact_metadata').document(contact_username).delete()
        contact_ref.collection('contact_metadata').document(uname).delete()

        conv_id = conversation_id(uname, contact_username)
        conv_ref = db.collection('conversations').document(conv_id)

        delete_collection(conv_ref.collection('messages'))
        conv_ref.delete()

        other_sid = online_users.get(contact_username)
        if other_sid:
            socketio.emit('force_contact_refresh', room=other_sid)

        emit('remove_contact_response', {
            'success': True,
            'contact_username': contact_username
        })

    except Exception as exc:
        print(f"Error removing contact: {exc}")
        traceback.print_exc()
        emit('remove_contact_response', {
            'success': False,
            'message': 'Could not remove contact.'
        })
     
    
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


if __name__ == '__main__':
    # Make sure this port configuration matches your Nginx virtual block allocation perfectly
    socketio.run(app, host='0.0.0.0', port=5555, allow_unsafe_werkzeug=True)