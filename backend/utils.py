from datetime import datetime, timezone
from backend.firebase_client import db


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

def conversation_id(username1, username2):
    return f"{min(username1, username2)}_{max(username1, username2)}"



def delete_collection(collection_ref, batch_size=50):
    docs = list(collection_ref.limit(batch_size).stream())

    while docs:
        batch = db.batch()

        for doc in docs:
            batch.delete(doc.reference)

        batch.commit()

        docs = list(collection_ref.limit(batch_size).stream())

