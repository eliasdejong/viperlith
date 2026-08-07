import os, fcntl, mmap
from collections import defaultdict
from collections.abc import Generator

import spsc_ring_threadsafe as srt

from src.config import WORKER_COUNT, QUEUE_SIZES


class Q:
	pass


def setup():
	q_dict = defaultdict(list)
	for i in range(WORKER_COUNT):
		path = os.getenv("SHM_PATH_PREFIX") + str(i)
		try:
			os.unlink(path)	# clear any previous allocations
		except FileNotFoundError:
			pass
		shm_size = sum(QUEUE_SIZES.values())
		fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
		os.ftruncate(fd, shm_size)
		m = mmap.mmap(fd, shm_size)
		os.close(fd)

def attach_all():
	q_dict = defaultdict(list)
	for i in range(WORKER_COUNT):
		path = os.getenv("SHM_PATH_PREFIX") + str(i)
		fd = os.open(path, os.O_RDWR)
		shm_size = sum(QUEUE_SIZES.values())
		m = mmap.mmap(fd, shm_size)
		os.close(fd)
		mv = memoryview(m)
		ofs = 0
		for ident, size in QUEUE_SIZES.items():
			q_dict[ident].append(mv[ofs:ofs + size])
			ofs += size
	for ident, q_list in q_dict.items():
		setattr(Q, ident, q_list)

def claim():
	fd = None
	for i in range(WORKER_COUNT):
		path = os.getenv("SHM_PATH_PREFIX") + str(i)
		try:
			fd = os.open(path, os.O_RDWR)
			fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
			print(f"Worker claimed ring number {i}", flush=True)
			break
		except OSError:
			if fd is not None:
				os.close(fd)
				fd = None
	if fd is None:
		raise Exception("Worker setup failed: unable to claim path")
	shm_size = sum(QUEUE_SIZES.values())
	m = mmap.mmap(fd, shm_size)
	mv = memoryview(m)
	ofs = 0
	for ident, size in QUEUE_SIZES.items():
		setattr(Q, ident, mv[ofs:ofs + size])
		ofs += size

def drain(q_list: list[memoryview]) -> Generator[bytes, None, None]:
	for ring in q_list:
		while True:
			try:
				yield srt.get(ring)
			except srt.QueueEmptyError:
				break