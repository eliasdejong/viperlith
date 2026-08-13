from typing import Annotated
import msgspec
from msgspec import Struct, Meta



UnixName = Annotated[
	str, Meta(min_length=1, max_length=32, pattern="^[a-z_][a-z0-9_-]*$")
]

Username = Annotated[
	str, Meta(min_length=1, max_length=32, pattern="[a-zA-Z0-9_ -]*$")
]

class InsertUser(Struct):
	session_id: str



class SendMessage(Struct):
	content: Annotated[str, Meta(min_length=1, max_length=500)]
	session_id: str | None = None

class SendMessageOuter(Struct):
	message: SendMessage

send_msg_decoder = msgspec.json.Decoder(type=SendMessageOuter)



class OpenChannel(Struct):
	name: UnixName
	session_id: str | None = None

class OpenChannelOuter(Struct):
	openChannel: OpenChannel

open_channel_decoder = msgspec.json.Decoder(type=OpenChannelOuter)



class CloseChannel(Struct):
	name: UnixName
	session_id: str | None = None

class CloseChannelOuter(Struct):
	closeChannel: CloseChannel

close_channel_decoder = msgspec.json.Decoder(type=CloseChannelOuter)



class SetNickname(Struct):
	nickname: Username
	session_id: str | None = None

class SetNicknameOuter(Struct):
	setNickname: SetNickname

set_nickname_decoder = msgspec.json.Decoder(type=SetNicknameOuter)