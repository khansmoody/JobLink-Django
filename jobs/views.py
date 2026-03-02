
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.db.models import Q

from .models import Job
from .models import JobApplication
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earch radius (in miles)
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def job_list(request):
    jobs = Job.objects.all()
    
    # User Story #20
    # hide flagged jobs from everyone except the admin and the recruiter who made it
    if not request.user.is_authenticated or request.user.role == 'job_seeker':
        jobs = jobs.filter(is_flagged=False)
    elif request.user.role == 'recruiter':
        jobs = jobs.filter(Q(is_flagged=False) | Q(recruiter=request.user))

    # Bring Filetering value
    title_query = request.GET.get('title')
    location_query = request.GET.get('location')
    min_salary = request.GET.get('min_salary')
    visa_support = request.GET.get('visa') # 'on' or None

    # Add filter only if there are conditions
    if title_query:
        jobs = jobs.filter(Q(title__icontains=title_query) | Q(skills__icontains=title_query))
    if location_query:
        jobs = jobs.filter(location__icontains=location_query)
    if min_salary:
        jobs = jobs.filter(salary_min__gte=min_salary)
    if visa_support == 'on':
        jobs = jobs.filter(visa_sponsorship=True)

    # --- [User Story 8] Distance Filtering logic
    user_lat = request.GET.get('lat')
    user_lon = request.GET.get('lon')
    radius = request.GET.get('radius')  # User can choose radius

    if user_lat and user_lon and radius:
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
            radius = float(radius)
            
            filtered_jobs = []
            for job in jobs:
                if job.latitude and job.longitude:
                    dist = calculate_distance(user_lat, user_lon, job.latitude, job.longitude)
                    if dist <= radius:
                        filtered_jobs.append(job)
            
            jobs = filtered_jobs  # Replace lists with closer jobs
        except ValueError:
            pass

    return render(request, 'jobs/jobs_list.html', {'jobs': jobs})

# Post/Create a Job (User Story #10)
@login_required
def job_post(request):
    if request.method == 'POST':
        Job.objects.create(
            title=request.POST.get('title', '').strip(),
            company_name=request.POST.get('company_name', '').strip(),
            description=request.POST.get('description', '').strip(),
            location=request.POST.get('location', '').strip(),
            skills=request.POST.get('skills', '').strip(),
            work_type=request.POST.get('work_type', 'onsite'),
            salary_min=request.POST.get('salary_min') or 0,
            salary_max=request.POST.get('salary_max') or 0,
            visa_sponsorship=bool(request.POST.get('visa_sponsorship')),
            recruiter=request.user,
        )
        return redirect('jobs:job_list')
    return render(request, 'jobs/jobs_post_edit.html')

# Edit an existing Job (User Story #10)
@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    if request.method == 'POST':
        job.title          = request.POST.get('title', '').strip()
        job.company_name   = request.POST.get('company_name', '').strip()
        job.description    = request.POST.get('description', '').strip()
        job.location       = request.POST.get('location', '').strip()
        job.skills         = request.POST.get('skills', '').strip()
        job.work_type      = request.POST.get('work_type', 'onsite')
        job.salary_min     = request.POST.get('salary_min') or 0
        job.salary_max     = request.POST.get('salary_max') or 0
        job.visa_sponsorship = bool(request.POST.get('visa_sponsorship'))
        job.save()
        return redirect('jobs:job_list')
    return render(request, 'jobs/jobs_post_edit.html', {'job': job})

@login_required
def apply_job(request, job_id):
    if request.user.role != "job_seeker":
        return redirect("jobs:job_list")

    if request.method == "POST" and request.POST.get("comment", "").strip() != "":
        job = get_object_or_404(Job, id=job_id)
        comment = request.POST["comment"].strip()
        application = JobApplication.objects.filter(job=job, user = request.user).first()
        if application:
            application.comment = comment
            application.save(update_fields=["comment"])
        else:
            application = JobApplication.objects.create(job=job, user = request.user, comment = comment )
    return redirect("jobs:job_list")

@login_required
def my_applications(request):
    if request.user.role != "job_seeker":
        return redirect("jobs:job_list")
    applications = (
        JobApplication.objects.filter(user=request.user).select_related("job")
        .order_by("-date")   
    )
    return render(request, "jobs/my_applications.html", {"applications": applications})

@login_required
def kanban(request):
    if request.user.role != "recruiter":
        return redirect("jobs:job_list")
    application = JobApplication.objects.filter(job__recruiter=request.user).select_related("job", "user").order_by("-date")
    grouped = {
        "applied": application.filter(status="applied"),
        "review": application.filter(status="review"),
        "interview": application.filter(status="interview"),
        "offer": application.filter(status="offer"),
        "closed": application.filter(status="closed"),
    }

    return render(request, "jobs/kanban.html", { "grouped": grouped})
