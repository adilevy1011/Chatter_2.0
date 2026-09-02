from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from gevent.threadpool import ThreadPoolExecutor

socketio = SocketIO(
    async_mode="gevent",
    logger=True,
    engineio_logger=True,
    cors_allowed_origins=[
        "https://chatter-2.com",
        "https://www.chatter-2.com"
    ],
)

limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"],
)

gevent_executor = ThreadPoolExecutor(max_workers=4)
