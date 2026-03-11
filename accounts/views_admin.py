from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import User

def admin_required(user):
    return getattr(user, "role", None) == "admin"

@user_passes_test(admin_required)
def user_list(request):
    users = User.objects.all().order_by("username")
    context = {
        "users": users,
        "total_count":     users.count(),
        "job_seeker_count": users.filter(role="job_seeker").count(),
        "recruiter_count":  users.filter(role="recruiter").count(),
        "admin_count":      users.filter(role="admin").count(),
    }
    return render(request, "accounts/admin_user_list.html", context)

@user_passes_test(admin_required)
def update_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        new_role = request.POST.get("role")
        if new_role in ["job_seeker", "recruiter", "admin"]:
            user.role = new_role
            user.save()
    return redirect("admin_user_list")
