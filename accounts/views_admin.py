from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
import csv
from accounts.models import User
from jobs.models import Job, JobApplication
from django.urls import reverse
from urllib.parse import urlencode


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

# User story 21 - Export CSV
@user_passes_test(admin_required)
def export_csv(request):
    export_type = request.GET.get('type', 'users')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{export_type}_export.csv"'

    writer = csv.writer(response)

    if export_type == 'users':
        writer.writerow(['Username', 'Email', 'First Name', 'Last Name', 'Role', 'Active', 'Date Joined'])
        for u in User.objects.all().order_by('username'):
            writer.writerow([
                u.username,
                u.email,
                u.first_name,
                u.last_name,
                u.role,
                u.is_active,
                u.date_joined.strftime('%Y-%m-%d'),
            ])

    elif export_type == 'jobs':
        writer.writerow(['Title', 'Company', 'Location', 'Work Type', 'Salary Min', 'Salary Max', 'Visa Sponsorship', 'Recruiter', 'Date Posted', 'Flagged'])
        for job in Job.objects.all().order_by('-created_at'):
            writer.writerow([
                job.title,
                job.company_name,
                job.location,
                job.work_type,
                job.salary_min,
                job.salary_max,
                job.visa_sponsorship,
                job.recruiter.username,
                job.created_at.strftime('%Y-%m-%d'),
                job.is_flagged,
            ])

    elif export_type == 'applications':
        writer.writerow(['Applicant', 'Job Title', 'Company', 'Status', 'Date Applied', 'Note'])
        for app in JobApplication.objects.all().select_related('user', 'job').order_by('-date'):
            writer.writerow([
                app.user.username,
                app.job.title,
                app.job.company_name,
                app.status,
                app.date.strftime('%Y-%m-%d'),
                app.comment,
            ])

    return response

def _admin_redirect(request):
    base   = reverse("admin_user_list")
    params = {}
    q = request.POST.get("q") or request.GET.get("q", "")
    r = request.POST.get("role_filter") or request.GET.get("role", "")
    if q: params["q"]    = q
    if r: params["role"] = r
    qs = urlencode(params)
    return f"{base}?{qs}" if qs else base
