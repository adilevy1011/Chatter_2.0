import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore_v1

cred = credentials.Certificate(os.path.expanduser("~/chatter-secrets/serviceAccountKey.json"))

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
db_async = firestore_v1.AsyncClient(project=db.project, credentials=cred.get_credential())
