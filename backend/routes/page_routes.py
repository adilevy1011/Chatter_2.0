import os
from flask import Response, send_from_directory

from backend.config import FRONTEND_FOLDER, PROJECT_ROOT


def register_page_routes(app):
    @app.route("/")
    def serve_index_gate():
        return send_from_directory(FRONTEND_FOLDER, "index.html")

    @app.route("/auth.html")
    def serve_identity_auth():
        return send_from_directory(FRONTEND_FOLDER, "auth.html")

    @app.route("/chat.html")
    def serve_chat_dashboard():
        return send_from_directory(FRONTEND_FOLDER, "chat.html")

    @app.route("/style.css")
    def style():
        return send_from_directory(
            FRONTEND_FOLDER,
            "style.css",
            mimetype="text/css"
        )

    @app.route("/app.js")
    def app_js():
        return send_from_directory(
            FRONTEND_FOLDER,
            "app.js",
            mimetype="application/javascript"
        )

    @app.route("/manifest.json")
    def manifest():
        return send_from_directory(
            FRONTEND_FOLDER,
            "manifest.json",
            mimetype="application/json"
        )

    @app.route("/sw.js")
    def service_worker():
        return send_from_directory(
            PROJECT_ROOT,
            "sw.js",
            mimetype="application/javascript"
        )

    @app.route("/api/vapid-public-key")
    def get_vapid_public_key():
        public_key = os.environ.get("VAPID_PUBLIC_KEY", "")
        return Response(public_key, mimetype="text/plain")

    @app.route("/reset-password.html")
    def serve_reset_password():
        return send_from_directory(FRONTEND_FOLDER, "reset-password.html")