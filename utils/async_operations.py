"""
utils/async_operations.py

This module provides async operation helpers for the Sage application.
It integrates the task queue system with the rest of the application
and provides common async operations.

Usage:
Import this module to perform non-blocking operations that improve application responsiveness.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union
import time
import functools
import threading

from utils.task_queue import global_task_queue, TaskStatus

def run_in_background(func=None, *, priority=0, daemon=True):
    """
    Decorator to run a function in the background using the global task queue.
    Can be used with or without parameters.
    
    Args:
        func: The function to decorate
        priority: Task priority level (higher = higher priority)
        daemon: Whether to use daemon threads (True) or non-daemon threads (False)
                Set to False for tasks like audio playback that should continue
                even when main thread exits
        
    Returns:
        Decorated function that submits task to background queue
        
    Usage:
        @run_in_background
        def long_running_task():
            pass
            
        @run_in_background(priority=10)
        def high_priority_task():
            pass
            
        @run_in_background(daemon=False)
        def audio_playback_task():
            pass
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logging.debug(f"Running {f.__name__} in background (daemon={daemon})")
            return global_task_queue.add_task(f, *args, priority=priority, daemon=daemon, **kwargs)
        return wrapper
    
    # Handle both @run_in_background and @run_in_background(priority=10) forms
    if func is None:
        return decorator
    return decorator(func)

def run_async(coroutine_func):
    """
    Decorator to run a coroutine function in a non-blocking way.
    
    Args:
        coroutine_func: Async function to run
        
    Returns:
        Decorated function that handles running the coroutine
        
    Usage:
        @run_async
        async def fetch_data():
            await asyncio.sleep(1)
            return "data"
    """
    @functools.wraps(coroutine_func)
    def wrapper(*args, **kwargs):
        async def run():
            return await coroutine_func(*args, **kwargs)
            
        # Use a dedicated thread for running the event loop
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run())
            loop.close()
            return result
            
        # Submit to task queue
        return global_task_queue.add_task(run_in_thread)
        
    return wrapper

def background_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get detailed status of a background task.
    
    Args:
        task_id: The ID of the task to check
        
    Returns:
        Dict containing task status information
    """
    status = global_task_queue.get_task_status(task_id)
    result = global_task_queue.get_task_result(task_id)
    
    return {
        'task_id': task_id,
        'status': status.value if status else 'unknown',
        'result': result if status == TaskStatus.COMPLETED else None,
        'is_complete': status == TaskStatus.COMPLETED,
        'is_failed': status == TaskStatus.FAILED
    }

def wait_for_task(task_id: str, timeout: float = None) -> Any:
    """
    Wait for a background task to complete and return its result.
    
    Args:
        task_id: The ID of the task to wait for
        timeout: Maximum time to wait in seconds (None = wait forever)
        
    Returns:
        The result of the task, or None if timeout occurred
        
    Raises:
        RuntimeError: If the task failed
    """
    start_time = time.time()
    
    while True:
        status = global_task_queue.get_task_status(task_id)
        
        if status == TaskStatus.COMPLETED:
            return global_task_queue.get_task_result(task_id)
            
        if status == TaskStatus.FAILED:
            raise RuntimeError(f"Background task {task_id} failed")
            
        if timeout is not None and (time.time() - start_time) > timeout:
            return None
            
        time.sleep(0.1)

def cleanup_old_tasks():
    """Clean up old completed tasks to prevent memory leaks"""
    global_task_queue.cleanup_completed_tasks()

# Initialize the task queue on module import
def initialize():
    """Initialize the async operations system"""
    global_task_queue.start()
    logging.info("Async operations system initialized")
    
    # Register cleanup on exit
    import atexit
    atexit.register(global_task_queue.stop)

# Auto-initialize
initialize()