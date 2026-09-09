import os


# identifier : size (bytes)
QUEUE_SIZES = {
	"user_insert": 4096,
	"msg_send": 65536,
	"channel_open": 4096,
	"channel_close": 4096,
	"nickname_set": 4096,
}