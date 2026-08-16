from typing import Annotated
import msgspec
from msgspec import Struct, Meta



UnixName = Annotated[
	str, Meta(min_length=1, max_length=32, pattern="^[a-z_][a-z0-9_-]*$")
]

Username = Annotated[
	str, Meta(min_length=1, max_length=32, pattern="^[A-Za-z0-9 _-]*$")
]

class UserInsert(Struct):
	session_id: str



class MessageSend(Struct):
	messageSend: Annotated[str, Meta(min_length=1, max_length=500)]
	session_id: str | None = None

msg_send_decoder = msgspec.json.Decoder(type=MessageSend)



class ChannelOpen(Struct):
	channelOpen: UnixName
	session_id: str | None = None

channel_open_decoder = msgspec.json.Decoder(type=ChannelOpen)



class ChannelClose(Struct):
	channelClose: UnixName
	session_id: str | None = None

channel_close_decoder = msgspec.json.Decoder(type=ChannelClose)



class NicknameSet(Struct):
	nicknameSet: Username
	session_id: str | None = None

nickname_set_decoder = msgspec.json.Decoder(type=NicknameSet)