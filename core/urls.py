from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.StudyHubLoginView.as_view(), name="login"),
    path("workspace/", views.workspace, name="workspace"),
    path("health/", views.health, name="health"),
]
