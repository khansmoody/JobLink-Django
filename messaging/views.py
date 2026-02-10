from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model

from .forms import MessageForm
from .models import Message

User = get_user_model()

@login_required
def inbox(request):
    messages = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
    partners = []
    seen_ids = set()

    for m in messages.order_by("-created_at"):
        other = m.receiver if m.sender == request.user else m.sender
        if other.id not in seen_ids:
            seen_ids.add(other.id)
            parters.append((other, m))
    return render(request, "messaging/inbox.html", {"partners": partners})

@login_required
def thread(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    conversation = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)
    ).order_by("created_at")
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = other_user
            msg.save()
            return redirect("messaging:thread", user_id=other_user.id)
    else:
        form = MessageForm()
    return render(request, "messaging/thread.html", {
        "other_user": other_user,
        "conversation": conversation,
        "form": form
    })