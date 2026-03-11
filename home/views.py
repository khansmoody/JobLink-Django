from django.shortcuts import render

def index(request):
    title = "GT HiveHire"
    if request.user.is_authenticated:
        display_name = request.user.first_name or request.user.username
        if request.user.role == "job_seeker":
            subtitle = "Ready to find your dream job?"
        elif request.user.role == "recruiter":
            subtitle = "Ready to find top talent faster?"
        else:
            subtitle = "Welcome back."
        welcome = f"Welcome back, {display_name}"
    else:
        welcome = "Welcome to HiveHire"
        subtitle = "Find your dream job or the perfect candidate here."

    template_data = {
        "title": title,
        "welcome": welcome,
        "subtitle": subtitle,
    }
    return render(request, "home/index.html", {"template_data": template_data})


def about(request):
    template_data = {}
    template_data['title'] = 'About HiveHire'
    return render(request, 'home/about.html', {'template_data': template_data})