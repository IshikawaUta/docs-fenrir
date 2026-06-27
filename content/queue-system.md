# Queue & Job System

Fenrir v4.1.0 includes a production-ready queue and job system for background processing.

## Overview

The queue system provides:

- **Job Management**: Create, track, and manage background jobs
- **Retry with Backoff**: Automatic retry with exponential backoff
- **Job Priorities**: Priority-based job ordering
- **Job Timeouts**: Configurable job execution timeouts
- **Worker Pools**: Concurrent job processing
- **Memory & Redis Backends**: In-memory for dev, Redis for production

## MemoryQueue

```python
from fenrir.queue import Queue, MemoryQueue, Worker

# Create queue
backend = MemoryQueue()
queue = Queue(backend)

# Register handler
@queue.handler("send_email")
async def send_email(to, subject, body):
    # Send email logic
    print(f"Email sent to {to}")

# Create worker
worker = Worker(queue, concurrency=5)

# Enqueue job
job = await queue.enqueue(
    "send_email",
    args=("user@example.com", "Welcome!", "Hello!"),
    priority=1,
    max_retries=3,
    timeout=30
)

# Start worker
await worker.start()
```

## RedisQueue

```python
from fenrir.queue import Queue, RedisQueue, Worker

# Create Redis queue
backend = RedisQueue(
    redis_url="redis://localhost:6379",
    prefix="myapp:jobs:"
)
queue = Queue(backend)

# Register handler
@queue.handler("process_order")
async def process_order(order_id):
    # Process order logic
    pass

# Create worker
worker = Worker(queue, concurrency=10)
```

## Job Configuration

```python
# Enqueue with options
job = await queue.enqueue(
    "task_name",
    args=(arg1, arg2),
    kwargs={"key": "value"},
    priority=0,          # Higher = more priority
    max_retries=3,       # Max retry attempts
    retry_delay=1.0,     # Base delay in seconds
    timeout=60,          # Timeout in seconds
    delay=10             # Delay before execution
)
```

## Job Status

```python
# Check job status
job = await queue.get_job(job_id)
print(job.status)      # "pending", "running", "completed", "failed"
print(job.result)      # Job result if completed
print(job.error)       # Error message if failed
print(job.retry_count) # Current retry count

# Get jobs by status
pending = await queue.get_jobs_by_status("pending")
running = await queue.get_jobs_by_status("running")
```

## Worker Configuration

```python
# Create worker with options
worker = Worker(
    queue,
    concurrency=10,     # Number of concurrent jobs
    poll_interval=0.1   # Seconds between polls
)

# Start worker
await worker.start()

# Stop worker gracefully
await worker.stop()
```

## Error Handling

```python
@queue.handler("risky_task")
async def risky_task(data):
    try:
        # Risky operation
        result = await process_data(data)
        return result
    except Exception as e:
        # Log error
        logger.error(f"Task failed: {e}")
        # Re-raise to trigger retry
        raise
```

## Job Cleanup

Completed jobs are automatically cleaned up after 60 seconds to prevent memory leaks:

```python
# Jobs are cleaned up automatically
# You can also manually remove jobs
await queue.remove_job(job_id)
```
