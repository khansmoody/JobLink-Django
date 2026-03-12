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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # User Story 5
    hide_email = models.BooleanField(default=False)
    hide_phone = models.BooleanField(default=False)
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public - Anyone can view my profile'),
            ('private', 'Private - Only I can view my profile'),
        ],
        default='public'
    )
    hide_full_name = models.BooleanField(default=False)
    hide_profile_photo = models.BooleanField(default=False)
    recruiter_contact_permission = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Recruiters'),
            ('none', 'No Recruiters'),
        ],
        default='all'
    )
    message_filtering = models.CharField(
        max_length=20,
        choices=[
            ('anyone', 'Accept messages from anyone'),
            ('connections', 'Connections only'),
            ('none', 'No messages'),
        ],
        default='anyone'
    )

    def display_name(self):
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full if full else self.user.username
    
     # User Story #9: Preferred commute radius
    preferred_commute_radius = models.IntegerField(
        default=25,
        choices=[
            (5, '5 miles'),
            (10, '10 miles'),
            (15, '15 miles'),
            (25, '25 miles'),
            (50, '50 miles'),
            (75, '75 miles'),
            (100, '100 miles'),
        ],
        help_text="Default distance filter for job searches"
    )

    def __str__(self):
        return f"Profile({self.display_name()})"
    
    def get_display_name(self, viewer_user=None):
        if self.hide_full_name:
            return self.user.username
        return self.display_name()

    def is_viewable_by(self, viewer_user):
        if self.user == viewer_user:
            return True
        if self.profile_visibility == 'private':
            return False
        return True
    
    def get_connection_count(self):
        return Connection.objects.filter(
            models.Q(from_user=self.user) | models.Q(to_user=self.user),
            status='accepted'
        ).count()
    
    def is_connected_to(self, other_user):
        if self.user == other_user:
            return False
        return Connection.objects.filter(
            models.Q(from_user=self.user, to_user=other_user) |
            models.Q(from_user=other_user, to_user=self.user),
            status='accepted'
        ).exists()

    def get_connection_status(self, other_user):
        if self.user == other_user:
            return None
        
        sent_request = Connection.objects.filter(
            from_user=self.user,
            to_user=other_user,
            status='pending'
        ).first()
        if sent_request:
            return 'pending_sent'
        
        received_request = Connection.objects.filter(
            from_user=other_user,
            to_user=self.user,
            status='pending'
        ).first()
        if received_request:
            return 'pending_received'
        
        if self.is_connected_to(other_user):
            return 'accepted'

        return None

# Connection Model 
# Represents a connection between two users (like LinkedIn connections).
class Connection(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='connections_sent'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='connections_received'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"
    
    def clean(self):
        if self.from_user == self.to_user:
            raise ValidationError("Users cannot connect with themselves.")

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

# User Story 15: Save Candidate Search
class SavedSearch(models.Model):
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_searches'
    )
    name = models.CharField(max_length=120)
    skill = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    project = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # Every time the recruiter *opens* this saved search we update this field
    # Profiles whose `updated_at` > last_checked are considered "new matches"
    last_checked = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (by {self.recruiter.username})"