from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse
from .models import User, JobSeekerProfile, Skill, Connection, SavedSearch
from django.core.mail import EmailMessage
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlencode
from django.utils import timezone
from .forms import (
    CustomUserCreationForm,
    CustomErrorList,
    SignUpForm,
    JobSeekerProfileForm,
    SkillsCSVForm,
    EducationFormSet,
    ExperienceFormSet,
    ExternalLinkFormSet,
    PrivacySettingsForm,
    AccountSettingsForm,
    EmailCandidateForm,
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
    
    # User Story 5
    # Check if profile is viewable based on privacy settings
    is_owner = request.user == target_user
    if not is_owner and profile.profile_visibility == 'private':
        messages.error(request, "This profile is set to private and cannot be viewed.")
        return redirect('accounts.connections')
    is_recruiter = request.user.role == 'recruiter' if request.user.is_authenticated else False
    
    connection_status = None
    connection_count = profile.get_connection_count()
    if not is_owner and request.user.role == 'job_seeker' and target_user.role == 'job_seeker':
        connection_status = profile.get_connection_status(request.user)
    
    context = {
        'template_data': {
            'title': f"{target_user.username} | Profile", 
            'profile': profile, 
            'is_owner': is_owner,
            'is_recruiter': is_recruiter,
            'connection_status': connection_status,
            'connection_count': connection_count,
        }
    }
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

# User Story 5
# Settings & Privacy View
@login_required
def settings_view(request):
    if request.user.role != 'job_seeker':
        raise PermissionDenied("Only job seekers can access privacy settings.")
    profile, _ = JobSeekerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'headline': 'Add your professional headline',
            'contact_email': request.user.email or '',
            'contact_phone': request.user.phone_number or '',
        }
    )
    
    if request.method == 'POST':
        if 'save_privacy' in request.POST:
            privacy_form = PrivacySettingsForm(request.POST, instance=profile)
            account_form = AccountSettingsForm()
            
            if privacy_form.is_valid():
                privacy_form.save()
                messages.success(request, "Privacy settings updated successfully.")
                return redirect('accounts.settings')
        
        elif 'delete_account' in request.POST:
            privacy_form = PrivacySettingsForm(instance=profile)
            account_form = AccountSettingsForm(request.POST)
            
            if account_form.is_valid() and account_form.cleaned_data.get('confirm_deletion'):
                username = request.user.username
                request.user.delete()
                messages.success(request, f"Account {username} has been permanently deleted.")
                return redirect('home.index')
            else:
                messages.error(request, "Please confirm account deletion by checking the box.")
    else:
        privacy_form = PrivacySettingsForm(instance=profile)
        account_form = AccountSettingsForm()

    context = {
        'template_data': {
            'title': 'Settings & Privacy',
            'privacy_form': privacy_form,
            'account_form': account_form,
            'profile': profile,
        }
    }
    return render(request, 'accounts/settings.html', context)

# Search for job seeker profiles so you can form connections or just look at others
# Was mostly for seeing if privacy settings (User story 5) was working or not
@login_required
def search_profiles(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        results = JobSeekerProfile.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(headline__icontains=query) |
            Q(location__icontains=query) |
            Q(skills__name__icontains=query)
        ).filter(
            user__role='job_seeker'
        ).distinct().select_related('user')
        
        results = [
            profile for profile in results 
            if profile.profile_visibility == 'public' or profile.user == request.user
        ]

        for profile in results:
            if profile.user != request.user:
                profile.connection_status_with_me = profile.get_connection_status(request.user)
                profile.connection_count = profile.get_connection_count()
            else:
                profile.connection_status_with_me = None
                profile.connection_count = profile.get_connection_count()
    
    context = {
        'template_data': {
            'title': 'Search Profiles',
            'query': query,
            'results': results,
            'result_count': len(results),
        }
    }
    return render(request, 'accounts/search.html', context)


# Send connection request
@login_required
def send_connection_request(request, username):
    if request.user.role != 'job_seeker':
        messages.error(request, "Only job seekers can send connection requests.")
        return redirect('home.index')
    
    to_user = get_object_or_404(User, username=username, role='job_seeker')
    
    if to_user == request.user:
        messages.error(request, "You cannot connect with yourself.")
        return redirect('accounts.profile_user', username=username)
    
    existing_connection = Connection.objects.filter(
        Q(from_user=request.user, to_user=to_user) |
        Q(from_user=to_user, to_user=request.user)
    ).first()
    
    if existing_connection:
        if existing_connection.status == 'pending':
            messages.info(request, "Connection request already pending.")
        elif existing_connection.status == 'accepted':
            messages.info(request, "You are already connected with this user.")
        return redirect('accounts.profile_user', username=username)
    
    Connection.objects.create(
        from_user=request.user,
        to_user=to_user,
        status='pending'
    )
    
    messages.success(request, f"Connection request sent to {to_user.username}.")
    return redirect('accounts.profile_user', username=username)


# Accept connection request
@login_required
def accept_connection(request, connection_id):
    connection = get_object_or_404(Connection, id=connection_id, to_user=request.user, status='pending')
    connection.status = 'accepted'
    connection.save()
    messages.success(request, f"You are now connected with {connection.from_user.username}.")
    return redirect('accounts.connections')


# Decline connection request
@login_required
def decline_connection(request, connection_id):
    connection = get_object_or_404(Connection, id=connection_id, to_user=request.user, status='pending')
    connection.status = 'declined'
    connection.save()
    messages.info(request, f"Connection request from {connection.from_user.username} declined.")
    return redirect('accounts.connections')


# Remove connection
@login_required
def remove_connection(request, username):
    other_user = get_object_or_404(User, username=username)
    connection = Connection.objects.filter(
        Q(from_user=request.user, to_user=other_user) |
        Q(from_user=other_user, to_user=request.user),
        status='accepted'
    ).first()
    
    if connection:
        connection.delete()
        messages.success(request, f"You are no longer connected with {other_user.username}.")
    else:
        messages.error(request, "Connection not found.")
    
    return redirect('accounts.profile_user', username=username)


# View all connections and pending requests
@login_required
def connections_list(request):
    if request.user.role != 'job_seeker':
        messages.error(request, "Only job seekers can view connections.")
        return redirect('home.index')
    
    accepted_connections = Connection.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='accepted'
    ).select_related('from_user', 'to_user', 'from_user__profile', 'to_user__profile')
    
    pending_received = Connection.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user', 'from_user__profile')
    
    pending_sent = Connection.objects.filter(
        from_user=request.user,
        status='pending'
    ).select_related('to_user', 'to_user__profile')
    
    connected_users = []
    for conn in accepted_connections:
        other_user = conn.to_user if conn.from_user == request.user else conn.from_user
        connected_users.append({
            'user': other_user,
            'profile': other_user.profile,
            'connection': conn,
        })
    
    context = {
        'template_data': {
            'title': 'My Connections',
            'connected_users': connected_users,
            'pending_received': pending_received,
            'pending_sent': pending_sent,
            'connection_count': len(connected_users),
            'pending_count': pending_received.count(),
        }
    }
    return render(request, 'accounts/connections.html', context)

# User Story #15: saved searches
@login_required
def candidate_search(request):
    if request.user.role != 'recruiter':
        return redirect('home.index')
    skill    = request.GET.get('skill', '').strip()
    location = request.GET.get('location', '').strip()
    project  = request.GET.get('project', '').strip()
    profiles = JobSeekerProfile.objects.filter(profile_visibility='public',user__role='job_seeker').select_related('user')

    if skill:
        profiles = profiles.filter(skills__name__icontains=skill).distinct()
    if location:
        profiles = profiles.filter(location__icontains=location)
    if project:
        profiles = profiles.filter(
            Q(experience_items__description__icontains=project) |
            Q(experience_items__title__icontains=project) |
            Q(about__icontains=project)
        ).distinct()

    saved_search = None
    new_match_ids = set()
    is_new_search = False
    saved_search_id = request.GET.get('saved_search_id')

    if saved_search_id:
        saved_search = get_object_or_404(SavedSearch, id=saved_search_id, recruiter=request.user)
        is_new_search = saved_search.last_checked == saved_search.created_at

        if is_new_search:
            new_match_ids = set(profiles.values_list('id', flat=True))
        else:
            new_match_ids = set(profiles.filter(updated_at__gt=saved_search.last_checked).values_list('id', flat=True))

        SavedSearch.objects.filter(pk=saved_search.pk).update(last_checked=timezone.now())

    candidate_list = []
    for profile in profiles:
        profile.is_new_match = profile.id in new_match_ids
        candidate_list.append(profile)

    # Recruiter's saved searches (for the panel)
    my_saved_searches = SavedSearch.objects.filter(recruiter=request.user)

    return render(request, 'accounts/candidate_list.html', {
        'candidates': candidate_list,
        'my_saved_searches': my_saved_searches,
        'saved_search': saved_search,
        'is_new_search': is_new_search,
        'current_skill': skill,
        'current_location': location,
        'current_project': project,
    })


# User Story #15: save a search
@login_required
def save_search(request):
    if request.user.role != 'recruiter' or request.method != 'POST':
        return redirect('candidate_search')
    name = request.POST.get('name', '').strip()
    skill = request.POST.get('skill', '').strip()
    location = request.POST.get('location', '').strip()
    project = request.POST.get('project', '').strip()
    if name:
        SavedSearch.objects.create(
            recruiter=request.user,
            name=name,
            skill=skill,
            location=location,
            project=project,
        )
    params = {}
    if skill:    params['skill']    = skill
    if location: params['location'] = location
    if project:  params['project']  = project
    base = reverse('candidate_search')
    qs = urlencode(params)
    return redirect(f"{base}?{qs}" if qs else base)


# User Story #15: delete a saved search
@login_required
def delete_saved_search(request, search_id):
    if request.user.role != 'recruiter' or request.method != 'POST':
        return redirect('candidate_search')

    saved_search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    saved_search.delete()
    return redirect('candidate_search')

# User Story #14: Email Candidate View
@login_required
def send_email_to_candidate(request, username):
    if request.user.role != 'recruiter':
        return JsonResponse({'success': False, 'error': 'Only recruiters can email candidates.'})
    try:
        candidate = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Candidate not found.'})
    candidate_email = candidate.email
    if not candidate_email:
        return JsonResponse({'success': False, 'error': 'Candidate has no email address.'})
    if request.method == 'POST':
        form = EmailCandidateForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message_body = form.cleaned_data['message']
            full_message = f"{message_body}\n\n"
            full_message += "---\n"
            full_message += f"Sent by {request.user.first_name or request.user.username}\n"
            full_message += "Recruiter on JobLink Platform"

            try:
                email = EmailMessage(
                    subject=subject,
                    body=full_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[candidate_email],
                    reply_to=[request.user.email] if request.user.email else [],
                ) 
                email.send(fail_silently=False)
                return JsonResponse({
                    'success': True,
                    'message': f'Email sent to {candidate.username} ({candidate_email})'
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to send: {str(e)}'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid form data'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})