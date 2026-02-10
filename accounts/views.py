from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import User, JobSeekerProfile, Skill
from .forms import (
    CustomUserCreationForm,
    CustomErrorList,
    SignUpForm,
    JobSeekerProfileForm,
    SkillsCSVForm,
    EducationFormSet,
    ExperienceFormSet,
    ExternalLinkFormSet,
)

# Logout
@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')

#Login
def login(request):
    template_data = {}
    template_data['title'] = 'Login'
    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(
            request,
            username = request.POST['username'],
            password = request.POST['password']
        )
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html', {'template_data': template_data})
        else:
            auth_login(request, user)
        
        # For our team!
        # If you want to send it to a different page for each role here, you can add the code as below
        # if user.role == 'recruiter':
            #     return redirect('recruiter_dashboard')

            return redirect('home.index')

def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html', {'template_data': template_data})
    elif request.method == 'POST':

        form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)
        if form.is_valid():
            form.save()
            return redirect('accounts.login')
        else:
            template_data['form'] = form
            return render(request, 'accounts/signup.html', {'template_data': template_data})

# User Story 1
# Profile display page
@login_required
def profile_view(request, username=None):
    target_user = request.user if username is None else get_object_or_404(User, username=username)
    profile, _ = JobSeekerProfile.objects.get_or_create(
        user=target_user,
        defaults={
            'headline': 'Add your professional headline',
            'contact_email': target_user.email or '',
            'contact_phone': target_user.phone_number or '',
        }
    )
    context = {'template_data': {'title': f"{target_user.username} | Profile", 'profile': profile, 'is_owner': request.user == target_user,}}
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    if request.user.role != 'job_seeker':
        raise PermissionDenied("Only job seekers can edit profiles.")

    profile, _ = JobSeekerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'headline': 'Add your professional headline',
            'contact_email': request.user.email or '',
            'contact_phone': request.user.phone_number or '',
        }
    )

    if request.method == 'POST':
        profile_form = JobSeekerProfileForm(request.POST, request.FILES, instance=profile)
        skills_form = SkillsCSVForm(request.POST)
        edu_formset = EducationFormSet(request.POST, instance=profile, prefix='edu')
        exp_formset = ExperienceFormSet(request.POST, instance=profile, prefix='exp')
        link_formset = ExternalLinkFormSet(request.POST, instance=profile, prefix='lnk')

        is_valid = all([
            profile_form.is_valid(),
            skills_form.is_valid(),
            edu_formset.is_valid(),
            exp_formset.is_valid(),
            link_formset.is_valid(),
        ])

        if is_valid:
            saved_profile = profile_form.save()
            request.user.first_name = profile_form.cleaned_data.get('first_name', '').strip()
            request.user.last_name = profile_form.cleaned_data.get('last_name', '').strip()
            request.user.email = saved_profile.contact_email
            request.user.phone_number = saved_profile.contact_phone
            request.user.save(update_fields=['first_name', 'last_name', 'email', 'phone_number'])
            edu_formset.save()
            exp_formset.save()
            link_formset.save()
            Skill.objects.filter(profile=profile).delete()
            for name in skills_form.cleaned_data['skills_csv']:
                Skill.objects.create(profile=profile, name=name)
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts.profile_me')
    else:
        profile_form = JobSeekerProfileForm(instance=profile)
        current_skills = ", ".join(profile.skills.values_list('name', flat=True))
        skills_form = SkillsCSVForm(initial={'skills_csv': current_skills})
        edu_formset = EducationFormSet(instance=profile, prefix='edu')
        exp_formset = ExperienceFormSet(instance=profile, prefix='exp')
        link_formset = ExternalLinkFormSet(instance=profile, prefix='lnk')

    context = {
        'template_data': {
            'title': 'Edit Profile',
            'profile_form': profile_form,
            'skills_form': skills_form,
            'edu_formset': edu_formset,
            'exp_formset': exp_formset,
            'link_formset': link_formset,
        }
    }
    return render(request, 'accounts/profile_edit.html', context)