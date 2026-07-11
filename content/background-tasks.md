# Background Tasks

Fenrir supports running background tasks after sending the response, allowing you to perform work like sending emails, processing data, or triggering webhooks without blocking the client.

## Simple Background Task

Use `BackgroundTasks` to run functions after the response is sent:

```python
from fenrir import BackgroundTasks

async def send_email_task(email: str, subject: str):
    print(f"Sending email to {email}: {subject}")
    await asyncio.sleep(2)
    print(f"Email sent to {email}")

@app.post("/send-email")
async def send_email(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email_task, "user@example.com", "Welcome!")
    return {"message": "Email queued"}
```

The task function receives positional arguments in the order they are passed.

## Multiple Background Tasks

Use `BackgroundTasks` to queue multiple tasks:

```python
from fenrir import BackgroundTasks

async def process_data(data_id: int):
    print(f"Processing data {data_id}")
    await asyncio.sleep(1)

async def send_notification(email: str):
    print(f"Sending notification to {email}")

@app.post("/tasks")
async def create_task(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_data, 1)
    background_tasks.add_task(send_notification, "user@example.com")
    return {"message": "Tasks queued"}
```

`BackgroundTasks` is automatically injected when declared as a parameter — no `Depends()` needed.

## Background Tasks in MethodView

Background tasks work seamlessly with class-based views:

```python
from fenrir import MethodView, BackgroundTasks

class ExportView(MethodView):
    async def post(self, background_tasks: BackgroundTasks):
        background_tasks.add_task(generate_report, "csv")
        background_tasks.add_task(send_notification, "admin@example.com")
        return {"export": "started"}
```

## Using Sanic-style Task Scheduler

Schedule recurring tasks using server lifecycle listeners:

```python
@app.listener("before_server_start")
async def setup_scheduler(app_instance):
    app_instance.add_task(scheduled_task())

async def scheduled_task():
    while True:
        print("Running scheduled task")
        await asyncio.sleep(60)
```

## Background Tasks with Dependency Injection

Background tasks can be used inside dependency-injected functions:

```python
from fenrir import Depends

async def verify_and_notify(background_tasks: BackgroundTasks):
    # Verify something
    background_tasks.add_task(log_audit_event, "user_verified")
    return True

@app.get("/verify")
async def verify(depends: bool = Depends(verify_and_notify)):
    return {"verified": True}
```

## Error Handling

If a background task raises an exception, it is logged but does not affect the client response. The exception is silently caught and logged by the framework.

## Best Practices

- **Keep tasks idempotent**: Background tasks may retry on failure, so design them to be safely re-runnable.
- **Avoid shared state**: Tasks run after the response, so avoid modifying request-scoped state.
- **Use async functions**: For I/O-bound work, use `async` functions to avoid blocking the event loop.
- **Limit task complexity**: For long-running or CPU-intensive work, consider using a dedicated task queue (Celery, RQ) instead.
