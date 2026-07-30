import os
import asyncio
from litestar import Litestar
from litestar.config.compression import CompressionConfig
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.static_files import create_static_files_router

import base64
from contextlib import asynccontextmanager

from src.util.session_id import get_session_id
from src.chat import router as chat_router


session_config = CookieBackendConfig(
	secret=base64.b64decode(os.getenv("SESSION_KEY"))
)

@asynccontextmanager
async def lifespan(app: Litestar):
	# setup
	yield
	# cleanup

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
		brotli_gzip_fallback=True,
	),
	dependencies={"sid": get_session_id},
)