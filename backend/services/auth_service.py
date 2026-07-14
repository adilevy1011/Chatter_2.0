from datetime import datetime, timezone, timedelta
from flask import request

from backend.config import TOKEN_MAX_AGE_DAYS
from backend.firebase_client import db
from backend.state import authenticated_sessions

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

