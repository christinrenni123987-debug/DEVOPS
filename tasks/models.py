from django.db import models


class Task(models.Model):
    """Replaces the MongoDB `tasks` collection."""

    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at", "-id"]


class TaskActivity(models.Model):
    """Replaces the PostgreSQL `task_activity` table. No foreign key on purpose:
    history must survive after a task is deleted (same as the original app)."""

    action = models.CharField(max_length=20)
    task_id = models.CharField(max_length=100)
    task_title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "task_activity"
        ordering = ["-created_at", "-id"]
