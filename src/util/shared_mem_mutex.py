"""
https://pypi.org/project/shared_memory_lock
license: MIT

Shared memory mutex implementation for blocking waits.

This mutex is designed for long waits (seconds to minutes) where processes
need to block without busy-waiting. Uses atomic operations with longer sleep
intervals compared to SharedMemoryLock.

Key features:
- Atomic operations for mutual exclusion
- Longer sleep intervals (10ms) for blocking waits
- Cross-platform (works on Linux, macOS, Windows)
- Suitable for queue operations and long critical sections
"""

import asyncio
import time
from multiprocessing import shared_memory
from typing import Any

from atomics import INT, atomicview

# State values
UNLOCKED = 0
LOCKED = 1


class SharedMemoryMutex:
	"""
	A blocking mutex backed by shared memory using atomic operations.

	This mutex uses longer sleep intervals (10ms) compared to SharedMemoryLock,
	making it suitable for:
	- Queue operations where processes wait for items
	- Long critical sections (seconds to minutes)
	- Scenarios where processes may wait without wasting CPU

	Usage:
		# Process A creates the mutex
		mutex = SharedMemoryMutex(name="my_mutex", create=True, run_id="app1")

		# Process B connects to the same mutex
		mutex = SharedMemoryMutex(name="my_mutex", create=False, run_id="app1")

		# Both processes can use it
		with mutex:
			# Critical section
			pass
	"""

	def __init__(self, name: str, create: bool = False, run_id: str = ""):
		"""
		Initialize a shared memory mutex.

		Args:
			name: Mutex name (used to identify the shared memory segment)
			create: Whether to create a new mutex or connect to existing
			run_id: Run identifier for namespacing

		Raises:
			FileNotFoundError: If create=False and mutex doesn't exist
		"""
		self.name = name
		self.run_id = run_id

		# Shared memory name for the mutex
		shm_name = f"{run_id}-{name}-mutex" if run_id else f"{name}-mutex"

		if create:
			# Create new shared memory for the mutex (4 bytes for atomic int32)
			self._shm = shared_memory.SharedMemory(name=shm_name, create=True, size=4)
		else:
			# Connect to existing shared memory mutex
			self._shm = shared_memory.SharedMemory(name=shm_name, create=False, size=4)

		# Create atomic view context over the shared memory buffer
		self._atomic_ctx = atomicview(self._shm.buf, INT)
		# Enter the context once and keep it open for the lifetime of the mutex
		self._atomic = self._atomic_ctx.__enter__()

		# Initialize to unlocked if creating
		if create:
			self._atomic.store(UNLOCKED)

		# Track cleanup state
		self._closed = False


	def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
		"""
		Acquire the mutex using atomic compare-and-swap.

		Args:
			blocking: Whether to block waiting for the mutex
			timeout: Maximum time to wait (only used if blocking=True)

		Returns:
			True if mutex was acquired, False if timeout or non-blocking failed
		"""
		start_time = time.time() if timeout is not None else None

		while True:
			# Try atomic compare-and-swap: if UNLOCKED (0), set to LOCKED (1)
			result = self._atomic.cmpxchg_weak(UNLOCKED, LOCKED)
			if result.success:
				return True

			if not blocking:
				return False

			# Check timeout
			if timeout is not None:
				elapsed = time.time() - start_time
				if elapsed >= timeout:
					return False

			# Sleep longer than spinlock (10ms vs 0.1ms) since mutex is for long waits
			time.sleep(0.01)

	def release(self) -> None:
		"""
		Release the mutex by setting state to UNLOCKED.
		"""
		self._atomic.store(UNLOCKED)

	async def acquire_async(self, timeout: float | None = None) -> bool:
		"""
		Async acquire the mutex.

		Args:
			timeout: Maximum time to wait in seconds (None = infinite)

		Returns:
			True if mutex was acquired, False if timeout
		"""
		start_time = time.time() if timeout is not None else None

		while True:
			# Try atomic compare-and-swap
			result = self._atomic.cmpxchg_weak(UNLOCKED, LOCKED)
			if result.success:
				return True

			# Check timeout
			if timeout is not None:
				elapsed = time.time() - start_time
				if elapsed >= timeout:
					return False

			# Async sleep to yield to event loop
			await asyncio.sleep(0.01)  # 10ms sleep

	async def __aenter__(self):
		"""Async context manager entry - acquire mutex."""
		await self.acquire_async()
		return self

	async def __aexit__(self, *args):
		"""Async context manager exit - release mutex."""
		self.release()

	def __enter__(self):
		"""Context manager entry - acquire mutex."""
		self.acquire()
		return self

	def __exit__(self, *args):
		"""Context manager exit - release mutex."""
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
			shm_name = f"{self.run_id}-{self.name}-mutex" if self.run_id else f"{self.name}-mutex"
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
		"""Restore from pickle - reconnect to shared memory."""
		self.__init__(name=state["name"], create=False, run_id=state["run_id"])
