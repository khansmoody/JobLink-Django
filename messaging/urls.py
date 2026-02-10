from django.urls import path
from . import views

app_name = "messaging"
urlpatterns = [
    path("", views.inbox, name="inbox"), path("thread/<int:user_id>/", views.thread, name="thread"),
]