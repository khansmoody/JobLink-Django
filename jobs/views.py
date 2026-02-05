from django.shortcuts import render
from django.db.models import Q
from .models import Job

def job_list(request):
    jobs = Job.objects.all()
    
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

    return render(request, 'jobs/job_list.html', {'jobs': jobs})
