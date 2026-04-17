import time
import asyncio
import logging
from abc import ABC, abstractmethod

# Setup logging for throttled requests
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RateLimiter")

class RequestAllowedState:
    """State object returned after limit check."""
    def __init__(self, allowed: bool, delay: float):
        self.allowed = allowed
        self.delay = delay


class RateLimiterStorage(ABC):
    """Abstract Base Class for modular storage backends (e.g., InMemory, Redis)."""
    @abstractmethod
    async def consume(self, identifier: str, amount: int, capacity: float, refill_rate: float, max_delay: float) -> RequestAllowedState:
        pass


class InMemoryStorage(RateLimiterStorage):
    """In-memory storage for rate limits, using Token Bucket algorithm."""
    def __init__(self):
        self.store = {}
        self.lock = asyncio.Lock()

    async def consume(self, identifier: str, amount: int, capacity: float, refill_rate: float, max_delay: float) -> RequestAllowedState:
        async with self.lock:
            now = time.monotonic()
            
            # Initialize new identifier
            if identifier not in self.store:
                self.store[identifier] = {"tokens": capacity, "last_update": now}
            
            state = self.store[identifier]
            
            # Refill tokens based on elapsed time
            elapsed = now - state["last_update"]
            state["tokens"] = min(capacity, state["tokens"] + elapsed * refill_rate)
            state["last_update"] = now
            
            # If tokens are immediately available
            if state["tokens"] >= amount:
                state["tokens"] -= amount
                return RequestAllowedState(allowed=True, delay=0.0)
            
            # Calculate wait time if we borrow from the future
            deficit = amount - state["tokens"]
            wait_time = deficit / refill_rate
            
            # Overloaded System -> Apply Backpressure Rejection
            if wait_time > max_delay:
                logger.warning(f"Throttled {identifier}: Rejecting request (Queue full, wait_time={wait_time:.2f}s > {max_delay}s)")
                return RequestAllowedState(allowed=False, delay=0.0)
            
            # Queue request -> Apply Backpressure Delay
            state["tokens"] -= amount
            logger.info(f"Backpressure for {identifier}: Delaying request for {wait_time:.2f}s")
            return RequestAllowedState(allowed=True, delay=wait_time)


class APIRateLimiter:
    """Core rate limiting layer that allows switching out backends easily."""
    def __init__(self, storage: RateLimiterStorage, capacity: float = 10.0, refill_rate: float = 5.0, max_delay: float = 5.0):
        self.storage = storage
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.max_delay = max_delay

    async def check_limit(self, identifier: str) -> RequestAllowedState:
        return await self.storage.consume(identifier, 1, self.capacity, self.refill_rate, self.max_delay)
