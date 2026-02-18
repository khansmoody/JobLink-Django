from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from accounts.models import User
from .models import Conversation, Message


def _is_recruiter(user):
    return getattr(user, "role", None) == "recruiter"


def _is_admin(user):
    return getattr(user, "role", None) == "admin"


@login_required
def inbox(request):
    """
    Shows all conversations for the logged-in user.
    """
    if _is_recruiter(request.user):
        convos = Conversation.objects.filter(recruiter=request.user).order_by("-created_at")
    else:
        # candidates (job_seekers) see their conversations
        convos = Conversation.objects.filter(candidate=request.user).order_by("-created_at")

    return render(request, "messaging/inbox.html", {"conversations": convos})


@login_required
def start_conversation(request, candidate_id):
    """
    Recruiter starts (or opens) a conversation with a candidate.
    """
    if not _is_recruiter(request.user):
        return HttpResponseForbidden("Only recruiters can start conversations.")

    candidate = get_object_or_404(User, id=candidate_id)

    convo, _ = Conversation.objects.get_or_create(
        recruiter=request.user,
        candidate=candidate
    )

    return redirect("messaging:chat", convo_id=convo.id)


@login_required
def chat(request, convo_id):
    """
    Chat thread view + send message.
    """
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
    return render(request, "messaging/chat.html", {
        "conversation": convo,
        "messages": messages
    })
