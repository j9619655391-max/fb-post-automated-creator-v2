from app.scheduler import token_guard_task

result = token_guard_task.delay()
print({"task_id": result.id})
print({"result": result.get(timeout=20, propagate=True)})

if not result.successful():
    raise SystemExit("Celery task did not complete successfully")
