from locust import HttpUser, task, between


class TodoUser(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(5)
    def list_tasks(self):
        self.client.get("/api/tasks")

    @task(2)
    def activity(self):
        self.client.get("/api/activity")

    @task(1)
    def health(self):
        self.client.get("/health/")
