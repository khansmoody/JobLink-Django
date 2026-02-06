from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from .models import User, JobSeekerProfile, Skill, Education, Experience, ExternalLink
from django import forms
from django.forms import inlineformset_factory

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

# User Story 1
# Web form for letting users input data
class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ['headline', 'location', 'about', 'profile_photo', 'banner_image']
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 220}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    # Clean up function similar to the one in accounts/models.py
    def clean_headline(self):
        headline = self.cleaned_data['headline'].strip()
        if not (1 <= len(headline) <= 220):
            raise forms.ValidationError("Headline must be between 1 and 220 characters.")
        return headline


# Creates a form for editing skills
class SkillsCSVForm(forms.Form):
    skills_csv = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Python, Adobe Photoshop, Java, Data Advertising'
        })
    )

    def clean_skills_csv(self):
        raw = self.cleaned_data.get('skills_csv', '')
        parts = [p.strip() for p in raw.split(',') if p.strip()]
        seen = set()
        deduped = []
        for p in parts:
            if len(p) > 50: # make sure not too long
                raise forms.ValidationError("Each skill must be <= 50 characters.")
            key = p.lower()
            if key not in seen: # make sure no dupes
                seen.add(key)
                deduped.append(p)
        return deduped


# Creates a web form for adding/editing education
class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        exclude = ['profile']
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-control'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        exclude = ['profile']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_type': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# Creates a web form for adding/editing links
class ExternalLinkForm(forms.ModelForm):
    class Meta:
        model = ExternalLink
        exclude = ['profile']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
        }