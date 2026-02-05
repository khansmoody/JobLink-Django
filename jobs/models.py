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
    visa_sponsorship = models.BooleanField(default=False)  # 비자 지원 여부
    
    # Management information
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_express_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"