from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health),  # used by Docker and Kubernetes probes
    path("api/health", views.health),  # original endpoint path
    path("api/health/", views.health),
    path("api/tasks", views.task_collection),
    path("api/tasks/", views.task_collection),
    path("api/tasks/<str:task_id>", views.task_detail),
    path("api/activity", views.activity_list),
]
