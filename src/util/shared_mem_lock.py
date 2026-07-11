"""
https://pypi.org/project/shared_memory_lock
license: MIT

Shared memory lock implementation for cross-process synchronization.

This lock can be created by name and accessed from any process, solving the
problem of multiprocessing.Lock not being picklable.
"""

import asyncio
import time
from multiprocessing import shared_memory
from typing import Any

from atomics import INT, atomicview


class SharedMemoryLock:
	"""
	A lock backed by shared memory that can be accessed by name from any process.

	This solves the pickling problem with multiprocessing.Lock - instead of trying
	to pickle the lock object, we just store the lock name and each process connects
	to the same shared memory lock by name.

	Uses a simple atomic flag (0 = unlocked, 1 = locked) with spin-lock semantics.

	Usage:
		# Process A creates the lock
		lock = SharedMemoryLock(name="my_lock", create=True, run_id="app1")

		# Process B connects to the same lock
		lock = SharedMemoryLock(name="my_lock", create=False, run_id="app1")

		# Both processes can use it
		with lock:
			# Critical section
			pass
	"""

	def __init__(self, name: str, create: bool = False, run_id: str = ""):
		"""
		Initialize a shared memory lock.

		Args:
			name: Lock name (used to identify the shared memory segment)
			create: Whether to create a new lock or connect to existing
			run_id: Run identifier for namespacing
		"""
		self.name = name
		self.run_id = run_id

		# Shared memory name for the lock
		shm_name = f"{run_id}-{name}-lock" if run_id else f"{name}-lock"

		if create:
			# Create new shared memory for the lock (4 bytes for atomic int32)
			self._shm = shared_memory.SharedMemory(name=shm_name, create=True, size=4)
			# Initialize to 0 (unlocked)
			import struct

			struct.pack_into("<i", self._shm.buf, 0, 0)
		else:
			# Connect to existing shared memory lock
			self._shm = shared_memory.SharedMemory(name=shm_name, create=False, size=4)

		# Create atomic view context over the shared memory buffer
		self._atomic_ctx = atomicview(self._shm.buf, INT)
		# Enter the context once and keep it open for the lifetime of the lock
		self._atomic = self._atomic_ctx.__enter__()
		# Track cleanup state
		self._closed = False

	def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
		"""
		Acquire the lock using atomic compare-and-swap.

		Args:
			blocking: Whether to block waiting for the lock
			timeout: Maximum time to wait (only used if blocking=True)

		Returns:
			True if lock was acquired, False if timeout or non-blocking and lock unavailable
		"""
		start_time = time.time() if timeout else None

		while True:
			# Atomic compare-and-swap: if current value is 0 (unlocked), set to 1 (locked)
			result = self._atomic.cmpxchg_weak(0, 1)
			if result.success:
				return True

			if not blocking:
				return False

			# Check timeout
			if timeout is not None:
				elapsed = time.time() - start_time
				if elapsed >= timeout:
					return False

			# Brief sleep to avoid busy-waiting
			time.sleep(0.0001)  # 100 microseconds

	def release(self) -> None:
		"""Release the lock atomically."""
		self._atomic.store(0)

	def __enter__(self):
		"""Context manager entry - acquire lock."""
		self.acquire()
		return self

	def __exit__(self, *args):
		"""Context manager exit - release lock."""
		self.release()

	async def acquire_async(self, timeout: float | None = None) -> bool:
		"""
		Async acquire the lock using atomic compare-and-swap.

		Args:
			timeout: Maximum time to wait

		Returns:
			True if lock was acquired, False if timeout
		"""
		start_time = time.time() if timeout else None

		while True:
			# Atomic compare-and-swap: if current value is 0 (unlocked), set to 1 (locked)
			result = self._atomic.cmpxchg_weak(0, 1)
			if result.success:
				return True

			# Check timeout
			if timeout is not None:
				elapsed = time.time() - start_time
				if elapsed >= timeout:
					return False

			# Async sleep to avoid blocking event loop
			await asyncio.sleep(0.0001)  # 100 microseconds

	async def __aenter__(self):
		"""Async context manager entry - acquire lock."""
		await self.acquire_async()
		return self

	async def __aexit__(self, *args):
		"""Async context manager exit - release lock."""
		self.release()

	def __del__(self):
		"""Destructor - ensure proper cleanup."""
		try:
			self.close()
		except Exception:
			pass

	def close(self) -> None:
		"""Close the shared memory connection."""
		if getattr(self, "_closed", True):
			return  # Already closed

		self._closed = True

		# Close the atomic context FIRST - it holds references to the buffer
		if hasattr(self, "_atomic_ctx") and self._atomic_ctx:
			try:
				self._atomic_ctx.__exit__(None, None, None)
			except Exception:
				pass
			finally:
				self._atomic_ctx = None
				self._atomic = None

		# Now close shared memory
		if hasattr(self, "_shm") and self._shm:
			try:
				self._shm.close()
			except Exception:
				pass
			finally:
				self._shm = None

	def unlink(self) -> None:
		"""Unlink (delete) the shared memory segment."""
		self.close()
		try:
			shm_name = f"{self.run_id}-{self.name}-lock" if self.run_id else f"{self.name}-lock"
			temp_shm = shared_memory.SharedMemory(name=shm_name)
			temp_shm.unlink()
			temp_shm.close()
		except FileNotFoundError:
			pass
		except Exception:
			pass

	def __getstate__(self) -> dict[str, Any]:
		"""Prepare for pickling - return connection info."""
		return {
			"name": self.name,
			"run_id": self.run_id,
		}

	def __setstate__(self, state: dict[str, Any]) -> None:
		"""Reconnect after unpickling in a new process."""
		self.name = state["name"]
		self.run_id = state["run_id"]

		# Reconnect to the same shared memory lock
		shm_name = f"{self.run_id}-{self.name}-lock" if self.run_id else f"{self.name}-lock"
		self._shm = shared_memory.SharedMemory(name=shm_name, create=False, size=4)

		# Create atomic view context over the shared memory buffer
		self._atomic_ctx = atomicview(self._shm.buf, INT)
		# Enter the context once and keep it open for the lifetime of the lock
		self._atomic = self._atomic_ctx.__enter__()
		# Track cleanup state
		self._closed = False
