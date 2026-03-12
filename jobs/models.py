from django.db import models
from django.conf import settings

class Job(models.Model):

    # Basic work info
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=100)
    description = models.TextField()
    
    location = models.CharField(max_length=100)
    skills = models.CharField(max_length=250)
    
    # Option to select
    WORK_TYPE_CHOICES = [
        ('remote', 'Remote'),
        ('onsite', 'On-site'),
        ('hybrid', 'Hybrid'),
    ]
    work_type = models.CharField(max_length=10, choices=WORK_TYPE_CHOICES, default='onsite')
    
    # Salary and Visa
    salary_min = models.IntegerField(default=0)
    salary_max = models.IntegerField(default=0)
    visa_sponsorship = models.BooleanField(default=False)
    
    # Management information
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # Checks to see if job post is spam (flags it) (User Story #20)
    is_flagged = models.BooleanField(default=False)


    # User Story #7: latitude, longitude to mark on map
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    @property
    def skills_list(self):
        """Returns skills as a cleaned list for template iteration."""
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def __str__(self):
        return f"{self.title} at {self.company_name}"

class JobApplication(models.Model):
    #Creates ID for an applications, comment(note), date, job, user
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('review', 'Review'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('closed', 'Closed'),
    ]
    status = models.CharField(max_length=20, choices = STATUS_CHOICES, default = 'applied')
    

    def __str__(self):
        return str(self.id) + ' - ' + self.job.title