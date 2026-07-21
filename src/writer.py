import os
import glob
import time


# SHM_PREFIX = "datastar-gpt-cmdqueue-"
# WRITER_STARTUP_TIMEOUT_SEC = 10.0

# cmdqueues = dict[int, None] = {}


# def startup():
# 	for path in glob.glob(f"/dev/shm/{SHM_PREFIX}*"):
# 		pid = int(os.path.basename(path).removeprefix(SHM_PREFIX))


# if __name__ == "__main__":
# 	startup()


print("Hello from writer!")