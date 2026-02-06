from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = (
        ('job_seeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
        ('admin', 'Administrator'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='job_seeker')
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# User Story 1
# Function that checks if an uploaded image is too big; for profile image and banner similar to LinkedIn
def validate_image_size(image, max_mb):
    if image and image.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Image is too large. Max allowed size is {max_mb}MB.")

# Function checks if a profile picture (avatar) is too big
def validate_avatar(image):
    validate_image_size(image, 5) # Size limit of 5 MB

# Function checks if a banner image (like a header image) is too big
def validate_banner(image):
    validate_image_size(image, 8) # Size limit of 8 MB

# Creates a database called "JobSeekerProfile" to store job seeker info
# Also connect the profile to a user account (one profile per user); that is what that OneToOneField is for
class JobSeekerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    # User Story 1 Fields
    headline = models.CharField(max_length=220)
    location = models.CharField(max_length=120, blank=True)
    about = models.TextField(blank=True)
    
    # Profile picture here
    profile_photo = models.ImageField(
        upload_to='profiles/avatars/',
        blank=True,
        null=True,
        validators=[validate_avatar]
    )
    
    # Banner image here (the big image at the top of their profile like in LinkedIn)
    banner_image = models.ImageField(
        upload_to='profiles/banners/',
        blank=True,
        null=True,
        validators=[validate_banner]
    )
    created_at = models.DateTimeField(auto_now_add=True) # auto records when this profile was first created
    updated_at = models.DateTimeField(auto_now=True) # same thing auto records last updated

    def __str__(self):
        return f"{self.user.username} Profile"