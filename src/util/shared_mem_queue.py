"""
https://pypi.org/project/shared-multiprocess-queue
license: MIT

Shared memory queue implementation for cross-process communication.

This queue can be created dynamically at runtime and accessed by name
from any process without requiring pickling or process restarts.
"""

from __future__ import annotations

import asyncio
import struct
import time
from multiprocessing import shared_memory
from typing import Any, Protocol

import cloudpickle

from shared_memory_lock import SharedMemoryLock, SharedMemoryMutex

# Queue layout in shared memory:
# [head: u64][tail: u64][capacity: u64][item_size: u64][data...]
_HEADER_FMT = "!QQQQ"  # head, tail, capacity, item_size
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)


class Observable(Protocol):
	"""Protocol for objects that can provide metrics."""

	def get_metrics(self) -> dict[str, Any]:
		"""Return metrics dictionary."""
		...


class SharedMemoryQueue:
	"""
	A FIFO queue backed by shared memory that can be created and accessed by name.

	This queue uses a ring buffer design with atomic head/tail pointers.
	Items are serialized using cloudpickle and stored in fixed-size slots.

	Usage:
		# Process A creates a queue
		queue = SharedMemoryQueue(name="work_queue", create=True, capacity=1000, run_id="app1")
		queue.put({"task": "data"})

		# Process B connects to it by name
		queue = SharedMemoryQueue(name="work_queue", create=False, run_id="app1")
		item = queue.get()
	"""

	def __init__(
		self,
		name: str,
		create: bool = False,
		capacity: int = 1000,
		item_size: int = 4096,
		run_id: str = "",
		lock: Any = None,
	):
		"""
		Initialize a shared memory queue.

		Args:
			name: Queue name (used to identify the shared memory segment)
			create: Whether to create a new queue or connect to existing
			capacity: Maximum number of items the queue can hold
			item_size: Maximum size of each serialized item in bytes
			run_id: Run identifier for namespacing
			lock: Ignored - SharedMemoryMutex (Linux) or SharedMemoryLock (fallback) is used
		"""
		self.name = name
		self.run_id = run_id
		self.capacity = capacity
		self.item_size = item_size

		# Use SharedMemoryMutex (efficient futex-based blocking)
		self._lock = SharedMemoryMutex(name=f"{name}_queue_lock", create=create, run_id=run_id)
		self._lock_type = "mutex"

		# Calculate total size needed
		data_size = capacity * item_size
		total_size = _HEADER_SIZE + data_size

		# Create or connect to shared memory
		shm_name = f"{run_id}-{name}-queue" if run_id else f"{name}-queue"
		self._shm = shared_memory.SharedMemory(name=shm_name, create=create, size=total_size)

		if create:
			# Initialize header: head=0, tail=0, capacity, item_size
			self._write_header(0, 0, capacity, item_size)
		else:
			# Read existing header to get queue parameters
			head, tail, cap, isize = self._read_header()
			self.capacity = cap
			self.item_size = isize

	def _read_header(self) -> tuple[int, int, int, int]:
		"""Read header: (head, tail, capacity, item_size)"""
		header_bytes = bytes(self._shm.buf[:_HEADER_SIZE])
		head, tail, capacity, item_size = struct.unpack(_HEADER_FMT, header_bytes)
		return int(head), int(tail), int(capacity), int(item_size)

	def _write_header(self, head: int, tail: int, capacity: int, item_size: int) -> None:
		"""Write header: (head, tail, capacity, item_size)"""
		header_bytes = struct.pack(_HEADER_FMT, head, tail, capacity, item_size)
		self._shm.buf[:_HEADER_SIZE] = header_bytes

	def _get_slot_offset(self, index: int) -> int:
		"""Calculate the offset for a given slot index"""
		slot_index = index % self.capacity
		return _HEADER_SIZE + (slot_index * self.item_size)

	def put(self, item: Any, block: bool = True, timeout: float | None = None) -> None:
		"""
		Put an item into the queue.

		Args:
			item: The item to enqueue
			block: Whether to block if queue is full
			timeout: Maximum time to wait if blocking

		Raises:
			Full: If queue is full and block=False or timeout expires
		"""
		start_time = time.time() if timeout else None

		while True:
			if self._lock:
				with self._lock:
					head, tail, capacity, item_size = self._read_header()

					# Check if queue is full
					if (tail - head) >= capacity:
						if not block:
							raise Full("Queue is full")
						if timeout and (time.time() - start_time) >= timeout:
							raise Full("Queue is full (timeout)")
						# Release lock before sleeping
					else:
						# Serialize the item
						try:
							item_bytes = cloudpickle.dumps(item)
						except Exception as e:
							raise ValueError(f"Failed to serialize item: {e}")

						if len(item_bytes) > item_size:
							raise ValueError(f"Item too large: {len(item_bytes)} bytes > {item_size} bytes")

						# Write item to tail slot
						slot_offset = self._get_slot_offset(tail)
						# Write item size first (4 bytes), then item data
						size_bytes = struct.pack("!I", len(item_bytes))
						self._shm.buf[slot_offset : slot_offset + 4] = size_bytes
						self._shm.buf[slot_offset + 4 : slot_offset + 4 + len(item_bytes)] = item_bytes

						# Update tail
						self._write_header(head, tail + 1, capacity, item_size)
						return
			else:
				head, tail, capacity, item_size = self._read_header()

				# Check if queue is full
				if (tail - head) >= capacity:
					if not block:
						raise Full("Queue is full")
				else:
					# Serialize the item
					try:
						item_bytes = cloudpickle.dumps(item)
					except Exception as e:
						raise ValueError(f"Failed to serialize item: {e}")

					if len(item_bytes) > item_size:
						raise ValueError(f"Item too large: {len(item_bytes)} bytes > {item_size} bytes")

					# Write item to tail slot
					slot_offset = self._get_slot_offset(tail)
					# Write item size first (4 bytes), then item data
					size_bytes = struct.pack("!I", len(item_bytes))
					self._shm.buf[slot_offset : slot_offset + 4] = size_bytes
					self._shm.buf[slot_offset + 4 : slot_offset + 4 + len(item_bytes)] = item_bytes

					# Update tail
					self._write_header(head, tail + 1, capacity, item_size)
					return

			# Queue was full - check timeout and sleep
			if timeout and (time.time() - start_time) > timeout:
				raise Full("Queue is full (timeout)")
			time.sleep(0.001)  # Brief sleep before retry

	def get(self, block: bool = True, timeout: float | None = None) -> Any:
		"""
		Get an item from the queue.

		Args:
			block: Whether to block if queue is empty
			timeout: Maximum time to wait if blocking

		Returns:
			The dequeued item

		Raises:
			Empty: If queue is empty and block=False or timeout expires
		"""
		start_time = time.time() if timeout else None

		while True:
			if self._lock:
				with self._lock:
					head, tail, capacity, item_size = self._read_header()

					# Check if queue is empty
					if head >= tail:
						if not block:
							raise Empty("Queue is empty")
						if timeout and (time.time() - start_time) >= timeout:
							raise Empty("Queue is empty (timeout)")
						# Release lock before sleeping
					else:
						# Read item from head slot
						slot_offset = self._get_slot_offset(head)
						# Read item size first
						size_bytes = bytes(self._shm.buf[slot_offset : slot_offset + 4])
						item_len = struct.unpack("!I", size_bytes)[0]

						# Read item data
						item_bytes = bytes(self._shm.buf[slot_offset + 4 : slot_offset + 4 + item_len])

						# Update head
						self._write_header(head + 1, tail, capacity, item_size)

						# Deserialize and return
						try:
							return cloudpickle.loads(item_bytes)
						except Exception as e:
							raise ValueError(f"Failed to deserialize item: {e}")
			else:
				head, tail, capacity, item_size = self._read_header()

				# Check if queue is empty
				if head >= tail:
					if not block:
						raise Empty("Queue is empty")
				else:
					# Read item from head slot
					slot_offset = self._get_slot_offset(head)
					# Read item size first
					size_bytes = bytes(self._shm.buf[slot_offset : slot_offset + 4])
					item_len = struct.unpack("!I", size_bytes)[0]

					# Read item data
					item_bytes = bytes(self._shm.buf[slot_offset + 4 : slot_offset + 4 + item_len])

					# Update head
					self._write_header(head + 1, tail, capacity, item_size)

					# Deserialize and return
					try:
						return cloudpickle.loads(item_bytes)
					except Exception as e:
						raise ValueError(f"Failed to deserialize item: {e}")

			# Queue was empty - check timeout and sleep
			if timeout and (time.time() - start_time) > timeout:
				raise Empty("Queue is empty (timeout)")
			time.sleep(0.001)  # Brief sleep before retry

	def put_nowait(self, item: Any) -> None:
		"""Put an item without blocking"""
		self.put(item, block=False)

	async def put_async(self, item: Any, timeout: float | None = None) -> None:
		"""
		Async put an item into the queue.

		Args:
			item: The item to enqueue
			timeout: Maximum time to wait

		Raises:
			Full: If queue is full and timeout expires
		"""
		start_time = time.time() if timeout else None

		while True:
			if self._lock:
				async with self._lock:
					head, tail, capacity, item_size = self._read_header()

					# Check if queue is full
					if (tail - head) >= capacity:
						if timeout and (time.time() - start_time) >= timeout:
							raise Full("Queue is full (timeout)")
						# Release lock before sleeping
					else:
						# Serialize the item
						try:
							item_bytes = cloudpickle.dumps(item)
						except Exception as e:
							raise ValueError(f"Failed to serialize item: {e}")

						if len(item_bytes) > item_size:
							raise ValueError(f"Item too large: {len(item_bytes)} bytes > {item_size} bytes")

						# Write item to tail slot
						slot_offset = self._get_slot_offset(tail)
						# Write item size first (4 bytes), then item data
						size_bytes = struct.pack("!I", len(item_bytes))
						self._shm.buf[slot_offset : slot_offset + 4] = size_bytes
						self._shm.buf[slot_offset + 4 : slot_offset + 4 + len(item_bytes)] = item_bytes

						# Update tail
						self._write_header(head, tail + 1, capacity, item_size)
						return
			else:
				# No lock mode
				head, tail, capacity, item_size = self._read_header()

				# Check if queue is full
				if (tail - head) >= capacity:
					if timeout and (time.time() - start_time) >= timeout:
						raise Full("Queue is full (timeout)")
				else:
					# Serialize the item
					try:
						item_bytes = cloudpickle.dumps(item)
					except Exception as e:
						raise ValueError(f"Failed to serialize item: {e}")

					if len(item_bytes) > item_size:
						raise ValueError(f"Item too large: {len(item_bytes)} bytes > {item_size} bytes")

					# Write item to tail slot
					slot_offset = self._get_slot_offset(tail)
					# Write item size first (4 bytes), then item data
					size_bytes = struct.pack("!I", len(item_bytes))
					self._shm.buf[slot_offset : slot_offset + 4] = size_bytes
					self._shm.buf[slot_offset + 4 : slot_offset + 4 + len(item_bytes)] = item_bytes

					# Update tail
					self._write_header(head, tail + 1, capacity, item_size)
					return

			# Queue was full - check timeout and sleep
			if timeout and (time.time() - start_time) > timeout:
				raise Full("Queue is full (timeout)")
			await asyncio.sleep(0.001)  # Brief async sleep before retry

	async def get_async(self, timeout: float | None = None) -> Any:
		"""
		Async get an item from the queue.

		Args:
			timeout: Maximum time to wait

		Returns:
			The dequeued item

		Raises:
			Empty: If queue is empty and timeout expires
		"""
		start_time = time.time() if timeout else None

		while True:
			if self._lock:
				async with self._lock:
					head, tail, capacity, item_size = self._read_header()

					# Check if queue is empty
					if head >= tail:
						if timeout and (time.time() - start_time) >= timeout:
							raise Empty("Queue is empty (timeout)")
						# Release lock before sleeping
					else:
						# Read item from head slot
						slot_offset = self._get_slot_offset(head)
						# Read item size first
						size_bytes = bytes(self._shm.buf[slot_offset : slot_offset + 4])
						item_len = struct.unpack("!I", size_bytes)[0]

						# Read item data
						item_bytes = bytes(self._shm.buf[slot_offset + 4 : slot_offset + 4 + item_len])

						# Update head
						self._write_header(head + 1, tail, capacity, item_size)

						# Deserialize and return
						try:
							return cloudpickle.loads(item_bytes)
						except Exception as e:
							raise ValueError(f"Failed to deserialize item: {e}")
			else:
				# No lock mode
				head, tail, capacity, item_size = self._read_header()

				# Check if queue is empty
				if head >= tail:
					if timeout and (time.time() - start_time) >= timeout:
						raise Empty("Queue is empty (timeout)")
				else:
					# Read item from head slot
					slot_offset = self._get_slot_offset(head)
					# Read item size first
					size_bytes = bytes(self._shm.buf[slot_offset : slot_offset + 4])
					item_len = struct.unpack("!I", size_bytes)[0]

					# Read item data
					item_bytes = bytes(self._shm.buf[slot_offset + 4 : slot_offset + 4 + item_len])

					# Update head
					self._write_header(head + 1, tail, capacity, item_size)

					# Deserialize and return
					try:
						return cloudpickle.loads(item_bytes)
					except Exception as e:
						raise ValueError(f"Failed to deserialize item: {e}")

			# Queue was empty - check timeout and sleep
			if timeout and (time.time() - start_time) > timeout:
				raise Empty("Queue is empty (timeout)")
			await asyncio.sleep(0.001)  # Brief async sleep before retry

	def put_batch(self, items: list[Any]) -> None:
		"""
		Put multiple items atomically under a single lock acquisition.

		Writes all items directly to the ring buffer in one operation.

		Args:
			items: List of items to enqueue

		Raises:
			Full: If queue doesn't have space for all items
		"""
		if not items:
			return

		if self._lock:
			with self._lock:
				# Read current state
				head, tail, capacity, item_size = self._read_header()

				# Check if we have space for all items
				current_size = tail - head
				if current_size + len(items) > capacity:
					raise Full(f"Queue full: {current_size}/{capacity}, cannot add {len(items)} items")

				# Serialize all items first
				serialized_items = []
				for item in items:
					try:
						item_bytes = cloudpickle.dumps(item)
					except Exception as e:
						raise ValueError(f"Failed to serialize item: {e}")

					if len(item_bytes) > item_size:
						raise ValueError(f"Item too large: {len(item_bytes)} bytes > {item_size} bytes")

					serialized_items.append(item_bytes)

				# Write all items to consecutive slots
				for item_bytes in serialized_items:
					slot_offset = self._get_slot_offset(tail)
					# Write item size first (4 bytes), then item data
					size_bytes = struct.pack("!I", len(item_bytes))
					self._shm.buf[slot_offset : slot_offset + 4] = size_bytes
					self._shm.buf[slot_offset + 4 : slot_offset + 4 + len(item_bytes)] = item_bytes
					tail += 1

				# Update header once with new tail
				self._write_header(head, tail, capacity, item_size)
		else:
			# Read current state
			head, tail, capacity, item_size = self._read_header()

			# Check if we have space for all items
			current_size = tail - head
			if current_size + len(items) > capacity:
				raise Full(f"Queue full: {current_size}/{capacity}, cannot add {len(items)} items")

			# Serialize all items first
			serialized_items = []
			for item in items:
				try:
					item_bytes = cloudpickle.dumps(item)
				except Exception as e:
					raise ValueError(f"Failed to serialize item: {e}")

				if len(item_bytes) > item_size:
					raise ValueError(f"Item too large: {len(item_bytes)} bytes > {item_size} bytes")

				serialized_items.append(item_bytes)

			# Write all items to consecutive slots
			for item_bytes in serialized_items:
				slot_offset = self._get_slot_offset(tail)
				# Write item size first (4 bytes), then item data
				size_bytes = struct.pack("!I", len(item_bytes))
				self._shm.buf[slot_offset : slot_offset + 4] = size_bytes
				self._shm.buf[slot_offset + 4 : slot_offset + 4 + len(item_bytes)] = item_bytes
				tail += 1

			# Update header once with new tail
			self._write_header(head, tail, capacity, item_size)

	def get_nowait(self) -> Any:
		"""Get an item without blocking"""
		return self.get(block=False)

	def empty(self) -> bool:
		"""Check if queue is empty"""
		head, tail, _, _ = self._read_header()
		return head >= tail

	def full(self) -> bool:
		"""Check if queue is full"""
		head, tail, capacity, _ = self._read_header()
		return (tail - head) >= capacity

	def qsize(self) -> int:
		"""Get approximate queue size"""
		head, tail, _, _ = self._read_header()
		return max(0, tail - head)

	def close(self) -> None:
		"""Close the shared memory connection"""
		if hasattr(self, "_shm") and self._shm:
			try:
				self._shm.close()
			except Exception:
				pass
		if hasattr(self, "_lock") and self._lock:
			try:
				self._lock.close()
			except Exception:
				pass

	def unlink(self) -> None:
		"""Unlink (delete) the shared memory segment"""
		self.close()
		try:
			shm_name = f"{self.run_id}-{self.name}-queue" if self.run_id else f"{self.name}-queue"
			temp_shm = shared_memory.SharedMemory(name=shm_name)
			temp_shm.unlink()
			temp_shm.close()
		except FileNotFoundError:
			pass
		except Exception:
			pass

		# Unlink the lock
		if hasattr(self, "_lock") and self._lock:
			try:
				self._lock.unlink()
			except Exception:
				pass

	def get_metrics(self) -> dict[str, Any]:
		"""
		Returns metrics for this queue.

		Implements Observable protocol.
		"""
		try:
			head, tail, capacity, item_size = self._read_header()
			size = max(0, tail - head)
			return {
				"queue_size": size,
				"queue_capacity": capacity,
				"queue_utilization_percent": (size / capacity * 100) if capacity > 0 else 0.0,
				"queue_item_size_bytes": item_size,
			}
		except Exception:
			return {}

	def __getstate__(self) -> dict[str, Any]:
		"""
		Prepare for pickling - return only connection info, not the lock.

		The lock cannot be pickled and must be created fresh in each process.
		"""
		return {
			"name": self.name,
			"run_id": self.run_id,
			"capacity": self.capacity,
			"item_size": self.item_size,
		}

	def __setstate__(self, state: dict[str, Any]) -> None:
		"""
		Reconnect after unpickling in a new process.

		Reconnects to the same shared memory lock and data segment.
		"""
		self.name = state["name"]
		self.run_id = state["run_id"]
		self.capacity = state["capacity"]
		self.item_size = state["item_size"]

		# Reconnect to the same shared memory mutex
		self._lock = SharedMemoryMutex(name=f"{self.name}_queue_lock", create=False, run_id=self.run_id)
		self._lock_type = "mutex"

		# Reconnect to existing shared memory
		shm_name = f"{self.run_id}-{self.name}-queue" if self.run_id else f"{self.name}-queue"
		total_size = _HEADER_SIZE + (self.capacity * self.item_size)
		self._shm = shared_memory.SharedMemory(name=shm_name, create=False, size=total_size)


class Empty(Exception):
	"""Raised when queue is empty"""

	pass


class Full(Exception):
	"""Raised when queue is full"""

	pass
