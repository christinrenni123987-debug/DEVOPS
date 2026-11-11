import json
from datetime import timezone as dt_timezone

from django.db import connection, transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from .models import Task, TaskActivity


def _iso(value):
    return value.astimezone(dt_timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _task_json(task):
    # Same field names the Express/MongoDB API returned, so the existing frontend keeps working.
    return {
        "_id": str(task.pk),
        "title": task.title,
        "completed": task.completed,
        "createdAt": _iso(task.created_at),
        "updatedAt": _iso(task.updated_at),
    }


def _activity_json(a):
    return {
        "id": str(a.pk),
        "action": a.action,
        "task_id": a.task_id,
        "task_title": a.task_title,
        "created_at": _iso(a.created_at),
    }


def _error(message, status):
    return JsonResponse({"error": message}, status=status)


def _read_json(request):
    """Returns a dict, or None if the body is not valid JSON."""
    if not request.body:
        return {}
    try:
        data = json.loads(request.body)
    except ValueError:
        return None
    return data if isinstance(data, dict) else {}


def _parse_title(body):
    title = body.get("title")
    if not isinstance(title, str):
        return None, "Task title is required."
    title = title.strip()
    if not title:
        return None, "Task title cannot be empty."
    if len(title) > 200:
        return None, "Task title must be 200 characters or fewer."
    return title, None


def _valid_id(value):
    return value.isascii() and value.isdigit() and str(int(value)) == value and 0 < int(value) < 2**63


def _record(action, task_id, title):
    TaskActivity.objects.create(action=action, task_id=str(task_id), task_title=title)


@require_http_methods(["GET", "POST"])
def task_collection(request):
    if request.method == "GET":  # READ
        return JsonResponse([_task_json(t) for t in Task.objects.all()], safe=False)

    body = _read_json(request)  # CREATE
    if body is None:
        return _error("Invalid JSON body.", 400)
    title, err = _parse_title(body)
    if err:
        return _error(err, 400)
    with transaction.atomic():
        task = Task.objects.create(title=title)
        _record("created", task.pk, task.title)
    return JsonResponse(_task_json(task), status=201)


@require_http_methods(["PATCH", "DELETE"])
def task_detail(request, task_id):
    if not _valid_id(task_id):
        return _error("Invalid task ID.", 400)

    if request.method == "DELETE":  # DELETE
        with transaction.atomic():
            task = Task.objects.select_for_update().filter(pk=task_id).first()
            if task is None:
                return _error("Task not found.", 404)
            title = task.title
            task.delete()
            _record("deleted", task_id, title)
        return HttpResponse(status=204)

    body = _read_json(request)  # UPDATE
    if body is None:
        return _error("Invalid JSON body.", 400)
    updates = {}
    if "title" in body:
        title, err = _parse_title(body)
        if err:
            return _error(err, 400)
        updates["title"] = title
    if "completed" in body:
        if not isinstance(body["completed"], bool):
            return _error("Completed must be true or false.", 400)
        updates["completed"] = body["completed"]
    if not updates:
        return _error("Provide a title and/or completed value to update.", 400)

    with transaction.atomic():
        task = Task.objects.select_for_update().filter(pk=task_id).first()
        if task is None:
            return _error("Task not found.", 404)
        for field, value in updates.items():
            setattr(task, field, value)
        task.save()
        _record("updated", task.pk, task.title)
    return JsonResponse(_task_json(task))


@require_GET
def activity_list(_request):
    rows = TaskActivity.objects.order_by("-created_at", "-id")[:20]
    return JsonResponse([_activity_json(a) for a in rows], safe=False)


@require_GET
def health(_request):
    """200 only when the app can reach MariaDB, otherwise 503."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "degraded", "database": "disconnected"}, status=503)
    return JsonResponse({"status": "ok", "database": "connected"})
