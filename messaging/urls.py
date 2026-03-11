from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("start/<int:candidate_id>/", views.start_conversation, name="start_conversation"),
    path("chat/<int:convo_id>/", views.chat, name="chat"),
    path("with/<int:user_id>/", views.start_with_user, name="start_with_user"),
]
