from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.StudyHubLoginView.as_view(), name="login"),
    path("logout/", views.StudyHubLogoutView.as_view(), name="logout"),
    path("workspace/", views.workspace, name="workspace"),
    path("health/", views.health, name="health"),
]
