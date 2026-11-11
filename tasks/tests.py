import json

from django.test import TestCase

from .models import Task, TaskActivity


def post(c, url, data):
    return c.post(url, json.dumps(data), content_type="application/json")


def patch(c, url, data):
    return c.patch(url, json.dumps(data), content_type="application/json")


class TaskApiTests(TestCase):
    def test_full_crud_and_activity(self):
        r = post(self.client, "/api/tasks", {"title": "  Buy milk  "})
        self.assertEqual(r.status_code, 201)
        task = r.json()
        self.assertEqual(task["title"], "Buy milk")
        self.assertFalse(task["completed"])
        self.assertEqual(set(task), {"_id", "title", "completed", "createdAt", "updatedAt"})

        self.assertEqual(len(self.client.get("/api/tasks").json()), 1)

        r = patch(self.client, f"/api/tasks/{task['_id']}", {"completed": True})
        self.assertTrue(r.json()["completed"])

        self.assertEqual(self.client.delete(f"/api/tasks/{task['_id']}").status_code, 204)
        self.assertEqual(self.client.get("/api/tasks").json(), [])

        actions = [a["action"] for a in self.client.get("/api/activity").json()]
        self.assertEqual(actions, ["deleted", "updated", "created"])
        self.assertEqual(Task.objects.count(), 0)
        self.assertEqual(TaskActivity.objects.count(), 3)

    def test_validation_errors(self):
        self.assertEqual(post(self.client, "/api/tasks", {}).status_code, 400)
        self.assertEqual(post(self.client, "/api/tasks", {"title": "   "}).status_code, 400)
        self.assertEqual(post(self.client, "/api/tasks", {"title": "x" * 201}).status_code, 400)
        self.assertEqual(patch(self.client, "/api/tasks/abc", {"completed": True}).status_code, 400)
        self.assertEqual(patch(self.client, "/api/tasks/999", {"completed": True}).status_code, 404)
        self.assertEqual(patch(self.client, "/api/tasks/999", {"completed": "yes"}).status_code, 400)
        self.assertEqual(patch(self.client, "/api/tasks/999", {}).status_code, 400)
        self.assertEqual(self.client.delete("/api/tasks/999").status_code, 404)

    def test_health(self):
        for url in ("/health/", "/api/health"):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["status"], "ok")
