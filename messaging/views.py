from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q

from accounts.models import User
from .models import Conversation, Message


def _is_recruiter(user):
    return getattr(user, "role", None) == "recruiter"


def _is_admin(user):
    return getattr(user, "role", None) == "admin"


@login_required
def inbox(request):
    convos = Conversation.objects.filter(Q(recruiter=request.user) | Q(candidate=request.user)).order_by("-created_at")
    return render(request, "messaging/inbox.html", {"conversations": convos})


@login_required
def start_conversation(request, candidate_id):
    if getattr(request.user, "role", None) != "recruiter":
        return HttpResponseForbidden("Only recruiters can use this endpoint.")

    candidate = get_object_or_404(User, id=candidate_id)

    convo, _ = Conversation.objects.get_or_create(
        recruiter=request.user,
        candidate=candidate
    )

    return redirect("messaging:chat", convo_id=convo.id)


@login_required
def chat(request, convo_id):
    convo = get_object_or_404(Conversation, id=convo_id)

    # access control: only participants can view
    if request.user != convo.recruiter and request.user != convo.candidate and not _is_admin(request.user):
        return HttpResponseForbidden("You do not have access to this conversation.")

    if request.method == "POST":
        content = (request.POST.get("message") or "").strip()
        if content:
            Message.objects.create(
                conversation=convo,
                sender=request.user,
                content=content
            )
        return redirect("messaging:chat", convo_id=convo.id)

    messages = convo.messages.select_related("sender").order_by("created_at")
    other = convo.candidate if request.user == convo.recruiter else convo.recruiter
    return render(request, "messaging/chat.html", {
        "conversation": convo,
        "messages": messages,
        "other_user": other,
    })

@login_required
def start_with_user(request, user_id):
    other = get_object_or_404(User, id=user_id)
    if other == request.user:
        return redirect("messaging:inbox")
    a, b = sorted([request.user, other], key=lambda u: u.id)
    convo, _ = Conversation.objects.get_or_create(recruiter=a, candidate=b)
    return redirect("messaging:chat", convo_id=convo.id)
