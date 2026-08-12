import os


WORKER_COUNT = max(1, os.cpu_count() - 1) if os.getenv("DEBUG") == "0" else 1

# identifier : size (bytes)
QUEUE_SIZES = {
	"insert_user": 4096,
	"send_msg": 4096,
	"open_channel": 4096,
}