import os


WORKER_COUNT = max(1, os.cpu_count() - 1) if os.getenv("DEBUG") == "0" else 1

# identifier : size (bytes)
QUEUE_SIZES = {
	"user_insert": 4096,
	"msg_send": 4096,
	"channel_open": 4096,
	"channel_close": 4096,
	"nickname_set": 4096,
}