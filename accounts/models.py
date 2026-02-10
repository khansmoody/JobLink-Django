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
        raise ValidationError(f"Image is too large. Maximum allowed is {max_mb}MB.")

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
    # Contact info fields
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=25, blank=True)
    website = models.URLField(blank=True)
    city_state = models.CharField(max_length=120, blank=True)
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

    # Returns user's full name or username
    def display_name(self):
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full if full else self.user.username

    def __str__(self):
        return f"Profile({self.display_name()})"

# Creates database table for storing skills
# Links these skills to the jobseeker profile
class Skill(models.Model):
    profile = models.ForeignKey(
        JobSeekerProfile,
        on_delete=models.CASCADE,
        related_name='skills'
    )
    name = models.CharField(max_length=50)
    class Meta:
        ordering = ['name'] # helps order by name so should order it alphabetically
    def __str__(self):
        return self.name

# Creates a database table for storing education info
# Links this to the jobseeker profile
class Education(models.Model):
    profile = models.ForeignKey(
        JobSeekerProfile, 
        on_delete=models.CASCADE,
        related_name='education_items'
    )
    school_name = models.CharField(max_length=160)
    degree = models.CharField(max_length=120, blank=True)
    field_of_study = models.CharField(max_length=120, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    class Meta:
        ordering = ['-end_date', '-start_date', '-id'] # sorts by most recent
    
    # Helps checks if the data makes sense before saving, for instance makes sure start date comes before end date
    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Education start date must be before or equal to end date.")
    
    def __str__(self):
        return self.school_name

# Creates a database table for storing work experience
class Experience(models.Model):
    profile = models.ForeignKey(
        JobSeekerProfile, 
        on_delete=models.CASCADE, 
        related_name='experience_items'
    )
    company_name = models.CharField(max_length=160)
    title = models.CharField(max_length=120)
    employment_type = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=120, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-is_current', '-end_date', '-start_date', '-id']
    
    # Similar to clean() function above just checking data makes sense
    def clean(self):
        if self.is_current and self.end_date is not None:
            raise ValidationError("Current role cannot have an end date.")

        if self.end_date and self.start_date > self.end_date:
            raise ValidationError("Experience start date must be before or equal to end date.")
    
    def __str__(self):
        return f"{self.title} @ {self.company_name}"

# Creates a database table for storing external links like a portfolio, GitHub, or etc.
class ExternalLink(models.Model):
    profile = models.ForeignKey(
        JobSeekerProfile, 
        on_delete=models.CASCADE, 
        related_name='links'
    )
    label = models.CharField(max_length=80)
    url = models.URLField(max_length=300)
    
    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.label