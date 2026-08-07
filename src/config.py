import os


WORKER_COUNT = max(1, os.cpu_count() - 1)

# identifier : size (bytes)
QUEUE_SIZES = {
	"insert_user_q": 4096,
	"send_msg_q": 4096,
}