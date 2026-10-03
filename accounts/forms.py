"""
accounts/forms.py
Registration and Login Forms
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from .models import StudentUser

# Kenya's 47 counties for dropdown
KENYA_COUNTIES = [
    ('', '-- Select County --'),
    ('Baringo', 'Baringo'), ('Bomet', 'Bomet'), ('Bungoma', 'Bungoma'),
    ('Busia', 'Busia'), ('Elgeyo-Marakwet', 'Elgeyo-Marakwet'),
    ('Embu', 'Embu'), ('Garissa', 'Garissa'), ('Homa Bay', 'Homa Bay'),
    ('Isiolo', 'Isiolo'), ('Kajiado', 'Kajiado'), ('Kakamega', 'Kakamega'),
    ('Kericho', 'Kericho'), ('Kiambu', 'Kiambu'), ('Kilifi', 'Kilifi'),
    ('Kirinyaga', 'Kirinyaga'), ('Kisii', 'Kisii'), ('Kisumu', 'Kisumu'),
    ('Kitui', 'Kitui'), ('Kwale', 'Kwale'), ('Laikipia', 'Laikipia'),
    ('Lamu', 'Lamu'), ('Machakos', 'Machakos'), ('Makueni', 'Makueni'),
    ('Mandera', 'Mandera'), ('Marsabit', 'Marsabit'), ('Meru', 'Meru'),
    ('Migori', 'Migori'), ('Mombasa', 'Mombasa'), ("Murang'a", "Murang'a"),
    ('Nairobi', 'Nairobi'), ('Nakuru', 'Nakuru'), ('Nandi', 'Nandi'),
    ('Narok', 'Narok'), ('Nyamira', 'Nyamira'), ('Nyandarua', 'Nyandarua'),
    ('Nyeri', 'Nyeri'), ('Samburu', 'Samburu'), ('Siaya', 'Siaya'),
    ('Taita-Taveta', 'Taita-Taveta'), ('Tana River', 'Tana River'),
    ('Tharaka-Nithi', 'Tharaka-Nithi'), ('Trans Nzoia', 'Trans Nzoia'),
    ('Turkana', 'Turkana'), ('Uasin Gishu', 'Uasin Gishu'),
    ('Vihiga', 'Vihiga'), ('Wajir', 'Wajir'), ('West Pokot', 'West Pokot'),
]

YEAR_CHOICES = [('', '-- Select Year --')] + [
    (str(y), str(y)) for y in range(2015, 2027)
]


class StudentRegistrationForm(forms.ModelForm):
    """
    Registration form for new students.
    Collects: name, email, school, year, county, password.
    """
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'id': 'id_password1'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat your password',
            'id': 'id_password2'
        })
    )

    class Meta:
        model = StudentUser
        fields = [
            'first_name', 'last_name', 'email',
            'school_name', 'year_completed', 'county', 'gender'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'your@email.com'
            }),
            'school_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. Alliance High School'
            }),
            'year_completed': forms.Select(
                choices=YEAR_CHOICES,
                attrs={'class': 'form-control'}
            ),
            'county': forms.Select(
                choices=KENYA_COUNTIES,
                attrs={'class': 'form-control'}
            ),
            'gender': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if StudentUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered. Please log in."
            )
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        # Generate username from email (required by AbstractUser)
        email = self.cleaned_data['email'].lower()
        # Usernames must be unique, but different emails can share a prefix
        # (john@gmail.com / john@yahoo.com), so append a counter if needed.
        base = email.split('@')[0][:140] or 'student'
        username = base
        suffix = 1
        while StudentUser.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base}{suffix}"
        user.username = username
        user.email = email
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class StudentLoginForm(AuthenticationForm):
    """
    Login form using email + password.
    """
    username = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your password'
        })
    )

    error_messages = {
        'invalid_login': (
            "Invalid email or password. Please try again."
        ),
        'inactive': "This account is inactive.",
    }
