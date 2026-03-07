from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Job, JobApplication
import math


# Phuong added state abbreviation for full name so "GA" and "Georgia" match the same jobs
STATE_ABBR = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
}
STATE_FULL = {v.upper(): k for k, v in STATE_ABBR.items()}


# Phuong added splits location query into tokens and expands abbreviations both ways
def expand_location_keywords(raw_query):
    tokens = [t.strip().upper() for t in raw_query.replace(',', ' ').split() if t.strip()]
    keywords = []
    for token in tokens:
        keywords.append(token)
        if token in STATE_ABBR:
            keywords.append(STATE_ABBR[token])
        elif token in STATE_FULL:
            keywords.append(STATE_FULL[token])
    return keywords


# US#8 — calculates straight-line distance in miles between two lat/lon points
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def job_list(request):
    jobs = Job.objects.all()

    # US#20 — hide flagged jobs from job seekers and non-logged-in users
    if not request.user.is_authenticated or request.user.role == 'job_seeker':
        jobs = jobs.filter(is_flagged=False)
    elif request.user.role == 'recruiter':
        jobs = jobs.filter(Q(is_flagged=False) | Q(recruiter=request.user))

    # keyword filter: title or skills
    title_query = request.GET.get('title', '').strip()
    if title_query:
        jobs = jobs.filter(
            Q(title__icontains=title_query) | Q(skills__icontains=title_query)
        )

    # US#8 — replaced simple icontains with keyword split + state abbreviation expansion
    location_query = request.GET.get('location', '').strip()
    if location_query:
        keywords = expand_location_keywords(location_query)
        loc_q = Q()
        for kw in keywords:
            loc_q |= Q(location__icontains=kw)
        jobs = jobs.filter(loc_q)

    # work type multi-checkbox filter
    work_types = request.GET.getlist('work_type')
    if work_types:
        jobs = jobs.filter(work_type__in=work_types)

    # minimum salary filter
    min_salary = request.GET.get('min_salary', '').strip()
    if min_salary:
        try:
            jobs = jobs.filter(salary_min__gte=int(min_salary))
        except ValueError:
            pass

    # visa sponsorship filter
    if request.GET.get('visa') == 'on':
        jobs = jobs.filter(visa_sponsorship=True)

    # US#8 "Han" — reads browser lat/lon + radius from GET params, filters jobs by haversine distance
    user_lat = request.GET.get('lat', '').strip()
    user_lon = request.GET.get('lon', '').strip()
    radius   = request.GET.get('radius', '').strip()

    if user_lat and user_lon and radius:
        try:
            user_lat_f = float(user_lat)
            user_lon_f = float(user_lon)
            radius_f   = float(radius)
            filtered = []
            for job in jobs:
                if job.latitude is not None and job.longitude is not None:
                    dist = calculate_distance(
                        user_lat_f, user_lon_f, job.latitude, job.longitude
                    )
                    if dist <= radius_f:
                        filtered.append(job)
            jobs = filtered
        except ValueError:
            pass

    # passes selected_work_types so template can re-check the right boxes after filtering
    return render(request, 'jobs/jobs_list.html', {
        'jobs': jobs,
        'selected_work_types': work_types,
    })


# US#10 — post a job
# US#17 — added lat/lon reading from hidden map pin fields and saving onto the Job record
@login_required
def job_post(request):
    if request.method == 'POST':
        # US#17 — parse lat/lon from hidden form fields submitted by the map pin
        lat_raw = request.POST.get('latitude', '').strip()
        lng_raw = request.POST.get('longitude', '').strip()
        try:
            latitude  = float(lat_raw) if lat_raw else None
            longitude = float(lng_raw) if lng_raw else None
        except ValueError:
            latitude = longitude = None

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
            latitude=latitude,   # US#17
            longitude=longitude, # US#17
        )
        return redirect('jobs:job_list')
    return render(request, 'jobs/jobs_post_edit.html')


# US#10 — edit a job
# US#17 — added lat/lon reading from hidden map pin fields and saving onto the Job record
@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    if request.method == 'POST':
        # US#17 — parse lat/lon from hidden form fields submitted by the map pin
        lat_raw = request.POST.get('latitude', '').strip()
        lng_raw = request.POST.get('longitude', '').strip()
        try:
            latitude  = float(lat_raw) if lat_raw else None
            longitude = float(lng_raw) if lng_raw else None
        except ValueError:
            latitude = longitude = None

        job.title            = request.POST.get('title', '').strip()
        job.company_name     = request.POST.get('company_name', '').strip()
        job.description      = request.POST.get('description', '').strip()
        job.location         = request.POST.get('location', '').strip()
        job.skills           = request.POST.get('skills', '').strip()
        job.work_type        = request.POST.get('work_type', 'onsite')
        job.salary_min       = request.POST.get('salary_min') or 0
        job.salary_max       = request.POST.get('salary_max') or 0
        job.visa_sponsorship = bool(request.POST.get('visa_sponsorship'))
        job.latitude         = latitude   # US#17
        job.longitude        = longitude  # US#17
        job.save()
        return redirect('jobs:job_list')
    return render(request, 'jobs/jobs_post_edit.html', {'job': job})


# apply for a job
@login_required
def apply_job(request, job_id):
    if request.user.role != "job_seeker":
        return redirect("jobs:job_list")
    if request.method == "POST" and request.POST.get("comment", "").strip():
        job = get_object_or_404(Job, id=job_id)
        comment = request.POST["comment"].strip()
        application = JobApplication.objects.filter(job=job, user=request.user).first()
        if application:
            application.comment = comment
            application.save(update_fields=["comment"])
        else:
            JobApplication.objects.create(job=job, user=request.user, comment=comment)
    return redirect("jobs:job_list")


# job seeker's application history
@login_required
def my_applications(request):
    if request.user.role != "job_seeker":
        return redirect("jobs:job_list")
    applications = (
        JobApplication.objects.filter(user=request.user)
        .select_related("job")
        .order_by("-date")
    )
    return render(request, "jobs/my_applications.html", {"applications": applications})


# recruiter kanban board
@login_required
def kanban(request):
    if request.user.role != "recruiter":
        return redirect("jobs:job_list")
    application = (
        JobApplication.objects.filter(job__recruiter=request.user)
        .select_related("job", "user")
        .order_by("-date")
    )
    grouped = {
        "applied":   application.filter(status="applied"),
        "review":    application.filter(status="review"),
        "interview": application.filter(status="interview"),
        "offer":     application.filter(status="offer"),
        "closed":    application.filter(status="closed"),
    }
    return render(request, "jobs/kanban.html", {"grouped": grouped})