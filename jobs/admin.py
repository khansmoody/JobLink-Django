from django.contrib import admin
from .models import Job, JobApplication

# User Story #20
# flag as spam
@admin.action(description='Flag selected jobs as spam/abuse')
def flag_as_spam(modeladmin, request, queryset):
    queryset.update(is_flagged=True)

# unflag
@admin.action(description='Unflag selected jobs')
def unflag_jobs(modeladmin, request, queryset):
    queryset.update(is_flagged=False)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'recruiter', 'is_flagged')
    actions = [flag_as_spam, unflag_jobs]

@admin.register(JobApplication)
class JobAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'user', 'status', 'date')