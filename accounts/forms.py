from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from .models import User

class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join([f'<div class="alert alert-danger" role="alert">{e}</div>' for e in self]))

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        # User need to type these fields when they sign up
        fields = ('username', 'email', 'role', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        
        # 중요: 회원가입 시 'Admin'은 선택 못하게 막고, 구직자/리크루터만 보이게 설정
        # Important: User can't select 'Admin', but only "job seeker" and "recruiter"
        self.fields['role'].choices = [
            ('job_seeker', 'Job Seeker'),
            ('recruiter', 'Recruiter'),
        ]

        # Apply bootstrap style to every field
        for fieldname in self.fields:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})