import os
import traceback
import uuid
from datetime import datetime, timezone, timedelta

from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from backend.config import TOKEN_MAX_AGE_DAYS, UPLOAD_FOLDER
from backend.firebase_client import db

def register_upload_routes(app):
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

