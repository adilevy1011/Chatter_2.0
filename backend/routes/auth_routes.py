import secrets
from datetime import datetime, timezone, timedelta

import bcrypt
from flask import jsonify, request

from backend.extensions import limiter
from backend.firebase_client import db
from backend.services.email_service import send_reset_email

def register_auth_routes(app):
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
