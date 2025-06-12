"""
utils/task_queue.py

This module provides a task queue system for asynchronous and parallel processing in the Sage application.
It allows non-critical operations to run in the background, improving overall responsiveness.

Classes:
- `TaskQueue`: A queue for managing asynchronous tasks.
- `Task`: Representation of an individual task with status tracking.

Usage:
Import this module to perform operations asynchronously without blocking the main thread.
"""

import asyncio
import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum
import time
import uuid

class TaskStatus(Enum):
    """Enum representing the status of a task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task:
    """
    Representation of an individual task with metadata and status tracking.
    """
    
    def __init__(self, func: Callable, *args, **kwargs):
        """
        Initialize a new task.
        
        Args:
            func: The function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        self.id = str(uuid.uuid4())
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.priority = kwargs.pop('priority', 0)  # Higher number = higher priority
        
    def execute(self) -> Any:
        """Execute the task and track its status"""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()
        
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
            return self.result
        except Exception as e:
            self.error = e
            self.status = TaskStatus.FAILED
            logging.error(f"Task {self.id} failed: {str(e)}")
            raise
        finally:
            self.completed_at = time.time()
            
    def cancel(self) -> bool:
        """
        Cancel the task if it hasn't started yet.
        
        Returns:
            bool: True if successfully cancelled, False otherwise
        """
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.CANCELLED
            return True
        return False
    
    def get_execution_time(self) -> Optional[float]:
        """Get execution time in seconds if the task has completed"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def __lt__(self, other):
        """Compare tasks based on priority for priority queue"""
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority > other.priority  # Higher priority first

class TaskQueue:
    """
    A queue manager for asynchronous tasks with priority support.
    """
    
    def __init__(self, max_workers: int = None):
        """
        Initialize the task queue.
        
        Args:
            max_workers: Maximum number of worker threads (defaults to number of CPUs)
        """
        self._tasks: Dict[str, Task] = {}
        self._task_queue = queue.PriorityQueue()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = False
        self._worker_thread = None
        self._results_callbacks = {}
        # Track non-daemon worker threads to prevent premature termination
        self._non_daemon_threads = []
    
    def start(self):
        """Start processing tasks in the queue"""
        if self._running:
            return
            
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logging.info("Task queue started")
    
    def stop(self):
        """Stop processing tasks"""
        self._running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        self._executor.shutdown(wait=False)
        
        # Wait for non-daemon threads (with short timeout to prevent hanging)
        for thread in self._non_daemon_threads[:]:
            if thread.is_alive():
                logging.info(f"Waiting for non-daemon thread to complete...")
                thread.join(timeout=0.5)
            self._non_daemon_threads.remove(thread)
            
        logging.info("Task queue stopped")
    
    def _process_queue(self):
        """Worker thread function that processes the queue"""
        while self._running:
            try:
                # Get next task with a timeout to allow checking _running flag
                priority, task = self._task_queue.get(timeout=1.0)
                
                # Skip cancelled tasks
                if task.status == TaskStatus.CANCELLED:
                    self._task_queue.task_done()
                    continue
                
                # Check if task should run in a daemon or non-daemon thread
                daemon = task.kwargs.pop('daemon', True)
                
                if daemon:
                    # Submit task to thread pool (daemon threads)
                    future = self._executor.submit(task.execute)
                    future.add_done_callback(lambda f, task_id=task.id: self._task_completed(task_id, f))
                else:
                    # Run in a dedicated non-daemon thread that will persist
                    thread = threading.Thread(
                        target=self._execute_in_non_daemon_thread,
                        args=(task,),
                        daemon=False
                    )
                    self._non_daemon_threads.append(thread)
                    thread.start()
                
            except queue.Empty:
                # No tasks in queue, just continue
                pass
            except Exception as e:
                logging.error(f"Error processing task queue: {e}")
    
    def _execute_in_non_daemon_thread(self, task: Task):
        """Execute a task in a non-daemon thread"""
        try:
            result = task.execute()
            # Manually handle callbacks since we're not using future callbacks
            if task.id in self._results_callbacks:
                for callback in self._results_callbacks[task.id]:
                    try:
                        callback(result)
                    except Exception as e:
                        logging.error(f"Error in task callback: {e}")
                # Clean up callbacks
                del self._results_callbacks[task.id]
        except Exception as e:
            logging.error(f"Error in non-daemon thread: {e}")
        finally:
            self._task_queue.task_done()
            # Clean up thread reference when done
            current_thread = threading.current_thread()
            if current_thread in self._non_daemon_threads:
                self._non_daemon_threads.remove(current_thread)
    
    def _task_completed(self, task_id: str, future):
        """Callback when a task is completed"""
        try:
            # Get result (will re-raise any exception from the task)
            result = future.result()
            
            # Call any callbacks registered for this task
            if task_id in self._results_callbacks:
                for callback in self._results_callbacks[task_id]:
                    try:
                        callback(result)
                    except Exception as e:
                        logging.error(f"Error in task callback: {e}")
                
                # Clean up callbacks
                del self._results_callbacks[task_id]
                
            self._task_queue.task_done()
            
        except Exception as e:
            logging.error(f"Task failed with error: {e}")
            self._task_queue.task_done()
    
    def add_task(self, func: Callable, *args, priority: int = 0, callback: Callable = None, daemon: bool = True, **kwargs) -> str:
        """
        Add a new task to the queue.
        
        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            priority: Task priority (higher number = higher priority)
            callback: Optional callback to run when task completes
            daemon: Whether to use daemon threads (True) or non-daemon threads (False)
                    Set to False for tasks like audio playback that should continue
                    even when main thread exits
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            str: Task ID
        """
        # Store daemon status in kwargs to be extracted during execution
        kwargs['daemon'] = daemon
        
        task = Task(func, *args, **kwargs)
        task_id = task.id
        
        self._tasks[task_id] = task
        
        if callback:
            if task_id not in self._results_callbacks:
                self._results_callbacks[task_id] = []
            self._results_callbacks[task_id].append(callback)
        
        # Add to queue with priority
        self._task_queue.put((priority, task))
        
        # Ensure the queue is running
        if not self._running:
            self.start()
            
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task by ID"""
        if task_id in self._tasks:
            return self._tasks[task_id].status
        return None
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get the result of a completed task"""
        if task_id in self._tasks and self._tasks[task_id].status == TaskStatus.COMPLETED:
            return self._tasks[task_id].result
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        if task_id in self._tasks:
            return self._tasks[task_id].cancel()
        return False
    
    def get_pending_tasks(self) -> List[str]:
        """Get IDs of all pending tasks"""
        return [tid for tid, task in self._tasks.items() 
                if task.status == TaskStatus.PENDING]
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all tasks"""
        return {
            tid: {
                'status': task.status.value,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'execution_time': task.get_execution_time()
            }
            for tid, task in self._tasks.items()
        }
    
    def cleanup_completed_tasks(self, max_age: float = 3600):
        """
        Remove completed/failed/cancelled tasks older than max_age seconds
        
        Args:
            max_age: Maximum age in seconds (default: 1 hour)
        """
        current_time = time.time()
        to_remove = []
        
        for tid, task in self._tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                if task.completed_at and (current_time - task.completed_at) > max_age:
                    to_remove.append(tid)
        
        for tid in to_remove:
            del self._tasks[tid]

# Create a global task queue instance that can be imported and used anywhere
global_task_queue = TaskQueue()