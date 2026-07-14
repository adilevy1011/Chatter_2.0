import os
import resend
from flask import Flask
from dotenv import load_dotenv

from backend.config import UPLOAD_FOLDER, MAX_UPLOAD_SIZE
from backend.extensions import socketio, limiter

def create_app():
    load_dotenv(os.path.expanduser("~/chatter-secrets/.env"))

    app = Flask(__name__, static_folder="public", static_url_path="/static")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    resend.api_key = os.environ.get("RESEND_API_KEY")

    socketio.init_app(app)
    limiter.init_app(app)

    from backend.routes.page_routes import register_page_routes
    from backend.routes.auth_routes import register_auth_routes
    from backend.routes.upload_routes import register_upload_routes

    from backend.sockets.lifecycle_sockets import register_lifecycle_sockets
    from backend.sockets.push_sockets import register_push_sockets
    from backend.sockets.auth_sockets import register_auth_sockets
    from backend.sockets.contact_sockets import register_contact_sockets
    from backend.sockets.conversation_sockets import register_conversation_sockets
    from backend.sockets.message_sockets import register_message_sockets
    from backend.sockets.group_sockets import register_group_sockets
    from backend.sockets.typing_sockets import register_typing_sockets

    register_page_routes(app)
    register_auth_routes(app)
    register_upload_routes(app)

    register_lifecycle_sockets()
    register_push_sockets()
    register_auth_sockets()
    register_contact_sockets()
    register_conversation_sockets()
    register_message_sockets()
    register_group_sockets()
    register_typing_sockets()

    return app
