from typing import Annotated
from msgspec import Struct, Meta




UnixName = Annotated[
	str, Meta(min_length=1, max_length=32, pattern="^[a-z_][a-z0-9_-]*$")
]

class Message(Struct):
	content: Annotated[str, Meta(min_length=1, max_length=500)]

