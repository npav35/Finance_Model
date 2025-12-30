import time
import functools
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class TimingEvent:
    name: str
    start_time: float
    end_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

class BenchmarkTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BenchmarkTracker, cls).__new__(cls)
            cls._instance.events = []
        return cls._instance

    def add_event(self, event: TimingEvent):
        self.events.append(event)

    def report(self):
        print("\n=== PERFORMANCE BENCHMARK REPORT ===")
        if not self.events:
            print("No events recorded.")
            return

        total_duration = 0.0
        print(f"{'Event Name':<30} | {'Duration (s)':<12} | {'Metadata'}")
        print("-" * 80)
        
        for event in self.events:
            duration = event.duration
            # specific logic to not double count nested events if we were doing that, 
            # but for now let's just list them.
            meta_str = str(event.metadata) if event.metadata else ""
            print(f"{event.name:<30} | {duration:<12.4f} | {meta_str}")

        print("-" * 80)

class Timer:
    def __init__(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.metadata = metadata or {}
        self.tracker = BenchmarkTracker()
        self.event = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        self.event = TimingEvent(
            name=self.name,
            start_time=self.start_time,
            end_time=end_time,
            metadata=self.metadata
        )
        self.tracker.add_event(self.event)

def time_it(name_fn=None):
    """Decorator to time a function. name_fn can be a string or a callable returning a string from args."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = name_fn if isinstance(name_fn, str) else func.__name__
            if callable(name_fn) and not isinstance(name_fn, str):
                 try:
                     name = name_fn(*args, **kwargs)
                 except:
                     name = func.__name__
            
            with Timer(name):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
             name = name_fn if isinstance(name_fn, str) else func.__name__
             if callable(name_fn) and not isinstance(name_fn, str):
                 try:
                     name = name_fn(*args, **kwargs)
                 except:
                     name = func.__name__

             with Timer(name):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

import asyncio
