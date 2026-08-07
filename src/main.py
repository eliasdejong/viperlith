import os, sys, time, subprocess
import uvicorn
import src.util.mpsc_queue as mpsc
from src.util.db_migration import run_migration
from src.config import WORKER_COUNT, QUEUE_SIZES



def main():
	mpsc.setup()
	run_migration()

	writer = subprocess.Popen([sys.executable, "-m", "src.single_writer"], env=os.environ.copy())
	
	if os.getenv("DEBUG") == "0":
		web = subprocess.Popen([
			sys.executable, "-m", "uvicorn", "src.web_worker:app",
			"--host", "0.0.0.0",
			"--port", "8000",
			"--loop", "uvloop",
			"--log-level", "warning",
			"--no-access-log",
			"--workers", str(WORKER_COUNT)
		], env=os.environ.copy())
	else:
		web = subprocess.Popen([
			sys.executable, "-m", "uvicorn", "src.web_worker:app",
			"--host", "127.0.0.1",
			"--port", "8000",
			"--loop", "uvloop",
			"--log-level", "debug",
			"--reload"
		], env=os.environ.copy())

	while writer.poll() is None and web.poll() is None:
		time.sleep(1)

	sys.exit(1)

if __name__ == "__main__":
	main()