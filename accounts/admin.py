from django.contrib import admin
from .models import User, JobSeekerProfile, Skill, Education, Experience, ExternalLink, Connection

# Register your models here.
# User Story 1
admin.site.register(User)
admin.site.register(JobSeekerProfile)
admin.site.register(Skill)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(ExternalLink)
admin.site.register(Connection)