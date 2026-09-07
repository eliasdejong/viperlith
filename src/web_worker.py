import os
import uvicorn
import base64
from contextlib import asynccontextmanager

from litestar import Litestar
from litestar.config.compression import CompressionConfig
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.static_files import create_static_files_router
from litestar.di import Provide

import src.util.mpsc_queue as mpsc
from src.util.db_read_con import con_pool_create
from src.util.session_id import get_session_id
from src.util.signals_json import signals_json
from src.chat.router import router as chat_router



session_config = CookieBackendConfig(
	secret=base64.b64decode(os.getenv("SESSION_KEY"))
)

@asynccontextmanager
async def lifespan(app: Litestar):
	# startup
	mpsc.claim() # must be called before creating any threads
	await con_pool_create()
	yield
	# shutdown

app = Litestar(
	debug=os.getenv("DEBUG") == "1",
	route_handlers=[
		chat_router,
		create_static_files_router(path="/static", directories=["static"]),
	],
	lifespan=[lifespan],
	middleware=[session_config.middleware],
	compression_config=CompressionConfig(
		backend="brotli",
		minimum_size=500,
		brotli_quality=3,
		brotli_mode="text",
		brotli_lgwin=21, # 2^21 = 2MB context window
		brotli_lgblock=0,
		brotli_gzip_fallback=False,
	),
	dependencies={
		"sid": Provide(get_session_id, sync_to_thread=False),
		"signals_json": Provide(signals_json),
	},
)