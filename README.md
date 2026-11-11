# To-Do CRUD App – Django + MariaDB

## Project Overview

This project is a Django rewrite of the original Node.js/Express to-do application. It preserves the original API endpoints and JSON response structure so that the existing `public/` frontend can work without modification.

The application uses MariaDB as its database and is containerized with Docker. It is also deployed to Kubernetes using Minikube, with persistent database storage and automatic application scaling.

## Technologies Used

- Python 3.12
- Django 5.2 LTS
- MariaDB 11.4
- Gunicorn
- PyMySQL
- Docker
- Docker Compose
- Kubernetes
- Minikube
- Locust

## 1. Run with Docker Compose

### Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose

### Configuration

Copy the example environment file:

```powershell
copy .env.example .env
```

Edit `.env` and configure the database passwords and Django secret key.

**Do not commit your real `.env` file to GitHub.**

### Build and start the application

```bash
docker compose up --build -d
```

Check the container status:

```bash
docker compose ps
```

The application and MariaDB containers should become healthy.

### Health check

```bash
curl http://localhost:3000/health/
```

The health endpoint returns HTTP 200 when MariaDB is reachable and HTTP 503 if the database connection fails.

### Open the application

http://localhost:3000

### Stop the application

```bash
docker compose down
```

The named MariaDB volume is retained, so database data remains available when the containers are started again.

To remove the containers and database volume:

```bash
docker compose down -v
```

**Warning:** The `-v` option deletes the persistent database volume and its stored data.

## 2. API Endpoints

The application preserves the original API functionality.

| HTTP Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tasks` | Retrieve all tasks |
| POST | `/api/tasks` | Create a new task |
| PATCH | `/api/tasks/<id>` | Update an existing task |
| DELETE | `/api/tasks/<id>` | Delete a task |
| GET | `/api/activity` | Retrieve the latest 20 activity entries |
| GET | `/health/` | Check application and database health |
| GET | `/api/health` | API health endpoint |

Task responses preserve the original JSON fields, including `_id`, `title`, `completed`, `createdAt` and `updatedAt`.

## 3. Automated Tests

The Django application tests can be executed without requiring a running MariaDB instance.

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the tests:

```bash
python manage.py test --settings=todo_project.settings_test
```

These tests verify application behaviour. They do not replace integration testing against a running MariaDB database.

## 4. Kubernetes Deployment

The application is deployed to a local Kubernetes cluster using Minikube.

### Kubernetes Architecture

The Kubernetes deployment consists of:

- A dedicated namespace named `todo-app`.
- A Django application Deployment.
- A MariaDB Deployment.
- A PersistentVolumeClaim for MariaDB data.
- A Kubernetes Secret for database credentials and the Django secret key.
- A ClusterIP Service for internal MariaDB communication.
- A NodePort Service for accessing the Django application.
- A HorizontalPodAutoscaler for automatic application scaling.

### Start Minikube

```bash
minikube start
```

### Build and load the application image

The Django Deployment uses the image `todo-django-app:1.0`.

Build the image:

```bash
docker build -t todo-django-app:1.0 .
```

Load it into Minikube:

```bash
minikube image load todo-django-app:1.0
```

### Apply Kubernetes manifests

Apply the namespace first:

```bash
kubectl apply -f k8s/namespace.yaml
```

Apply the Kubernetes Secret:

```bash
kubectl apply -f k8s/secret.yaml
```

Apply the MariaDB resources:

```bash
kubectl apply -f k8s/mariadb.yaml
```

Apply the Django application Deployment and Service:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

Apply the HorizontalPodAutoscaler:

```bash
kubectl apply -f k8s/hpa.yaml
```

*Note: Adjust the filenames above if your actual Kubernetes files use different names.*

### Verify the deployment

Check the pods:

```bash
kubectl get pods -n todo-app
```

Check the Services:

```bash
kubectl get services -n todo-app
```

Check persistent storage:

```bash
kubectl get pvc -n todo-app
```

Check the HorizontalPodAutoscaler:

```bash
kubectl get hpa -n todo-app
```

Check resource usage:

```bash
kubectl top pods -n todo-app
```

### Access the application

Use Minikube to retrieve the application URL:

```bash
minikube service todo-app -n todo-app --url
```

The application is exposed through a NodePort Service using port `30080`, forwarding traffic to the Django container on port `3000`.

## 5. Kubernetes Health Checks and Fault Tolerance

The Django Deployment uses Kubernetes health probes:

- **Startup probe:** Allows the application time to start.
- **Readiness probe:** Checks whether the application is ready to receive traffic.
- **Liveness probe:** Checks whether the application is responding.

The MariaDB Deployment uses a readiness probe to verify database availability.

MariaDB data is stored using a PersistentVolumeClaim mounted at `/var/lib/mysql`. This allows database data to survive MariaDB pod replacement.

The application Deployment uses resource requests and limits to define its CPU and memory requirements.

## 6. Horizontal Pod Autoscaling

The application uses a HorizontalPodAutoscaler with the following configuration:

| Setting | Value |
|---|---|
| Minimum replicas | 1 |
| Maximum replicas | 3 |
| Scaling metric | CPU utilization |
| CPU target utilization | 70% |

The HPA monitors CPU utilization relative to the CPU requests configured in the Django Deployment.

When CPU utilization increases beyond the target, Kubernetes can increase the number of application replicas. When demand decreases, the number of replicas can scale down again.

The assignment testing includes evidence of scaling from one to three replicas and subsequent scale-down behaviour.

The Kubernetes Metrics Server is required for CPU-based autoscaling.

## 7. Load Testing with Locust

Locust is used to simulate concurrent users accessing the application.

The load-testing scripts are stored in the `loadtest/` directory.

The assignment requires a test with at least 500 concurrent virtual users and a duration of at least 60 seconds.

The performance evaluation considers:

- Total number of requests.
- Requests per second (throughput).
- Average response time.
- Median response time.
- Response-time percentiles.
- Failed requests and error rate.
- CPU utilization.
- Memory utilization.
- Kubernetes pod scaling behaviour.

The measured results and performance analysis are documented in the project report.

Load-test failures are included in the analysis rather than being excluded from the results.

## 8. Assumptions and Design Decisions

### Database consolidation

The original application used MongoDB for task storage and PostgreSQL for activity logging.

Since the assignment requires MariaDB, both datasets were migrated into MariaDB tables:

- `tasks`
- `task_activity`

### Activity history

Activity records do not use a foreign key to the task table. This allows activity history to remain available even after a task has been deleted.

### API compatibility

The Django implementation preserves the original API endpoints and JSON response structure.

Task IDs are exposed as strings in `_id`, using auto-incrementing integer identifiers instead of MongoDB ObjectIds.

### Activity logging

Task changes and corresponding activity records are written within a single database transaction. This ensures that the task operation and its activity entry are committed together.

### Application port

Port `3000` is retained from the original application.

### Runtime and dependencies

The application uses Python 3.12, Django 5.2 LTS and MariaDB 11.4.

PyMySQL is used as a pure-Python MySQL/MariaDB driver, avoiding the need for a C compiler in the runtime image.

### Application server

Gunicorn is used instead of Django's development server.

The default configuration uses:

- 3 Gunicorn worker processes.
- 2 threads per worker.
- The `gthread` worker class.

These values are configurable through environment variables.

### Database migrations

Database migrations are executed automatically when the application container starts.

The entrypoint script retries database initialization if MariaDB is not yet ready.

### Middleware and authentication

The application is a stateless JSON API without user login or session functionality. CSRF and session middleware are therefore not configured.

### Allowed hosts

`ALLOWED_HOSTS` defaults to `*` to support local access and Kubernetes health probes. A production deployment should restrict this setting to trusted hostnames.

### Secrets and credentials

Database credentials and the Django secret key are supplied through environment variables.

For Docker Compose, these values are configured in `.env`.

For Kubernetes, credentials are supplied through a Kubernetes Secret.

Real credentials are not stored in version control.

### Database networking

MariaDB is not exposed through a host port. The Django application accesses MariaDB through the internal Docker network or Kubernetes Service.

## 9. Security Considerations

- The Django application runs as a non-root user inside the Docker container.
- Gunicorn is used as the production WSGI server.
- Database credentials are supplied through environment variables and Kubernetes Secrets.
- The local `.env` file is excluded from version control.
- The Docker runtime image uses the slim Python image.
- MariaDB is accessible internally rather than being published directly to the host.
- Demonstration credentials must be replaced before any non-local deployment.

## 10. Repository Contents

The repository contains the following project components:

| Component | Description |
|---|---|
| Django application | Backend API and application logic |
| `public/` | Existing frontend |
| `Dockerfile` | Multi-stage application image |
| `docker-compose.yaml` | Local application and database setup |
| `.env.example` | Example environment configuration |
| `.dockerignore` | Files excluded from Docker build context |
| `.gitignore` | Files excluded from Git |
| `requirements.txt` | Python dependencies |
| `k8s/` | Kubernetes manifests |
| `loadtest/` | Locust load-testing scripts |
| `README.md` | Project documentation |

## 11. Conclusion

The project demonstrates the migration of an existing Node.js/Express CRUD application to Django and MariaDB, followed by containerization and Kubernetes deployment.

Docker Compose provides a local development and testing environment, while Kubernetes provides application orchestration, persistent database storage, health monitoring and CPU-based horizontal scaling.

Load testing with Locust is used to evaluate application performance under concurrent user demand. The observed performance, errors, resource utilization and scaling behaviour are evaluated in the accompanying project report.
