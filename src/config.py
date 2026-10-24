import os


# identifier : size (bytes)
QUEUE_SIZES = {
	"user_insert": 8192,
	"msg_send": 131072,
	"channel_open": 8192,
	"channel_close": 8192,
	"nickname_set": 8192,
}