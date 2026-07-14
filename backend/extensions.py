from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from gevent.threadpool import ThreadPoolExecutor

socketio = SocketIO(
    async_mode="threading",
    cors_allowed_origins=[
        "https://chatter-2.com",
        "https://chatter-2.duckdns.org",
        "http://147.182.235.138:5555",
    ],
)

limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"],
)

gevent_executor = ThreadPoolExecutor(max_workers=4)
