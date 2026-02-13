from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from .models import User, JobSeekerProfile, Skill, Education, Experience, ExternalLink
from django import forms
from django.forms import inlineformset_factory

class CustomErrorList(ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ""
        items = "".join(f"<li>{e}</li>" for e in self)
        return mark_safe(f'<div class="alert alert-danger py-2 mb-2"><ul class="mb-0">{items}</ul></div>')

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

def apply_bootstrap_classes(form):
    for _, field in form.fields.items():
        widget = field.widget
        existing = widget.attrs.get("class", "")
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = (existing + " form-check-input").strip()
        else:
            widget.attrs["class"] = (existing + " form-control").strip()


class BootstrapErrorMixin:
    def _html_output(self, *args, **kwargs):
        output = super()._html_output(*args, **kwargs)
        output = output.replace(
            '<ul class="errorlist nonfield">',
            '<div class="alert alert-danger py-2 mb-2"><ul class="mb-0">'
        ).replace(
            '<ul class="errorlist">',
            '<div class="alert alert-danger py-2 mb-2"><ul class="mb-0">'
        ).replace('</ul>', '</ul></div>')
        return mark_safe(output)


class SignUpForm(BootstrapErrorMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'password1', 'password2']
        help_texts = {'username': '', 'password1': '', 'password2': ''}

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_class", CustomErrorList)
        super().__init__(*args, **kwargs)
        if hasattr(User, "ROLE_CHOICES") and "role" in self.fields:
            self.fields["role"].choices = [c for c in User.ROLE_CHOICES if c[0] != "admin"]
        apply_bootstrap_classes(self)

# User Story 1
# Web form for letting users input data
class JobSeekerProfileForm(BootstrapErrorMixin, forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            'headline', 'location', 'about',
            'contact_email', 'contact_phone', 'website',
            'profile_photo', 'banner_image'
        ]
        widgets = {
            'headline': forms.TextInput(attrs={'maxlength': 220, 'placeholder': 'e.g., Software Engineer looking for Summer 2026 internship'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Atlanta, GA'}),
            'about': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Short professional summary'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
            'contact_phone': forms.TextInput(attrs={'placeholder': '+1 123 456 7890'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://yourportfolio.com'}),
        }
    first_name = forms.CharField(
        required=False,
        max_length=150,
        label="First legal name",
        widget=forms.TextInput(attrs={"placeholder": "e.g., George"})
    )
    last_name = forms.CharField(
        required=False,
        max_length=150,
        label="Last legal name",
        widget=forms.TextInput(attrs={"placeholder": "e.g., Burdell"})
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_class", CustomErrorList)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.user_id:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name

        apply_bootstrap_classes(self)

    # Clean up function similar to the one in accounts/models.py
    def clean_headline(self):
        headline = (self.cleaned_data.get('headline') or '').strip()
        if not headline:
            raise forms.ValidationError("Headline is required.")
        if len(headline) > 220:
            raise forms.ValidationError("Headline must be 220 characters or fewer.")
        return headline

    def clean_website(self):
        website = (self.cleaned_data.get('website') or '').strip()
        if website and not (website.startswith('http://') or website.startswith('https://')):
            raise forms.ValidationError("Website URL must start with http:// or https://")
        return website

# Creates a form for editing skills
class SkillsCSVForm(BootstrapErrorMixin, forms.Form):
    skills_csv = forms.CharField(
        required=False,
        label='Skills',
        widget=forms.TextInput(attrs={'placeholder': 'Python, Adobe Photoshop, Java, Data Advertising'})
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_class", CustomErrorList)
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)

    def clean_skills_csv(self):
        raw = (self.cleaned_data.get('skills_csv') or '').strip()
        if not raw:
            return []
        parts = [p.strip() for p in raw.split(',') if p.strip()]
        deduped = []
        seen = set()
        for idx, skill in enumerate(parts, start=1):
            if len(skill) > 50: # make sure not too long
                raise forms.ValidationError(f"Skill #{idx} is too long. Max 50 chars.")
            key = skill.lower()
            if key not in seen: # make sure no dupes
                seen.add(key)
                deduped.append(skill)
        return deduped

# Creates a web form for adding/editing education
class EducationForm(BootstrapErrorMixin, forms.ModelForm):
    class Meta:
        model = Education
        exclude = ['profile']
        widgets = {
            'school_name': forms.TextInput(attrs={'placeholder': 'e.g., Georgia Tech'}),
            'degree': forms.TextInput(attrs={'placeholder': 'e.g., B.S. or Bachelors'}),
            'field_of_study': forms.TextInput(attrs={'placeholder': 'e.g., Computer Science'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Achievements, coursework, etc.'}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_class", CustomErrorList)
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and start > end:
            self.add_error("end_date", "End date must be after start date.")
        return cleaned

class ExperienceForm(BootstrapErrorMixin, forms.ModelForm):
    class Meta:
        model = Experience
        exclude = ['profile']
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': 'e.g., Microsoft'}),
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Software Engineer Intern'}),
            'employment_type': forms.TextInput(attrs={'placeholder': 'e.g., Internship'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Seattle, WA'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'is_current': forms.CheckboxInput(),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Impact, responsibilities, tools'}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_class", CustomErrorList)
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        is_current = cleaned.get("is_current")

        if is_current and end:
            self.add_error("end_date", "Leave end date blank for a current role.")
        if start and end and start > end:
            self.add_error("end_date", "End date must be after start date.")
        return cleaned

# Creates a web form for adding/editing links
class ExternalLinkForm(BootstrapErrorMixin, forms.ModelForm):
    class Meta:
        model = ExternalLink
        exclude = ['profile']
        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'e.g., GitHub'}),
            'url': forms.URLInput(attrs={'placeholder': 'https://github.com/yourname'}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_class", CustomErrorList)
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)

    def clean_url(self):
        url = (self.cleaned_data.get("url") or "").strip()
        if url and not (url.startswith("http://") or url.startswith("https://")):
            raise forms.ValidationError("URL must start with http:// or https://")
        return url

# User Story 5
# Privacy Settings
class PrivacySettingsForm(BootstrapErrorMixin, forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            'hide_email',
            'hide_phone',
            'profile_visibility',
            'hide_full_name',
            'hide_profile_photo',
            'recruiter_contact_permission',
            'message_filtering',
        ]
        widgets = {
            'hide_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hide_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hide_full_name': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hide_profile_photo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profile_visibility': forms.Select(attrs={'class': 'form-select'}),
            'recruiter_contact_permission': forms.Select(attrs={'class': 'form-select'}),
            'message_filtering': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'hide_email': 'Hide email address from recruiters',
            'hide_phone': 'Hide phone number from recruiters',
            'profile_visibility': 'Profile visibility',
            'hide_full_name': 'Hide full name, show username only',
            'hide_profile_photo': 'Hide profile picture from recruiters',
            'recruiter_contact_permission': 'Who can contact me',
            'message_filtering': 'Message filtering',
        }
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_class", CustomErrorList)
        super().__init__(*args, **kwargs)

# User Story 5 - 
# Account Settings
class AccountSettingsForm(BootstrapErrorMixin, forms.Form):
    confirm_deletion = forms.BooleanField(
        required=False,
        label='I understand that deleting my account is permanent and cannot be undone',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_class", CustomErrorList)
        super().__init__(*args, **kwargs)

# Added 'formsets' which allow users to add/edit/delete multiple items at once
# Users can add multiple schools, edit existing ones, or delete them which should be done all on one page
EducationFormSet = inlineformset_factory(JobSeekerProfile, Education, form=EducationForm, extra=1, can_delete=True)

ExperienceFormSet = inlineformset_factory(JobSeekerProfile, Experience, form=ExperienceForm, extra=1, can_delete=True)

ExternalLinkFormSet = inlineformset_factory(JobSeekerProfile, ExternalLink, form=ExternalLinkForm, extra=1, can_delete=True)

CustomUserCreationForm = SignUpForm
SignupForm = SignUpForm