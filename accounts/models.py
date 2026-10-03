"""
accounts/models.py
Custom Student User Model
Extends Django's AbstractUser to add Kenya-specific student fields.
Justification: The proposal requires student profiles with school name,
year of completion, and curriculum type — fields not in Django's default User.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class StudentUser(AbstractUser):
    """
    Custom user model for Kenyan secondary school graduates.
    Replaces Django's default User with additional student-specific fields.
    """

    CURRICULUM_CHOICES = [
        ('8-4-4', '8-4-4 (KCSE)'),
        # CBC to be added in future version as noted in proposal scope
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Prefer not to say'),
    ]

    # Override email to make it unique and required (used for login)
    email = models.EmailField(unique=True, null=False, blank=False)

    # Student-specific fields
    school_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of secondary school attended"
    )
    year_completed = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Year of KCSE completion e.g. 2024"
    )
    curriculum = models.CharField(
        max_length=10,
        choices=CURRICULUM_CHOICES,
        default='8-4-4'
    )
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )
    county = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="County of residence"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )
    profile_complete = models.BooleanField(
        default=False,
        help_text="True when grades + quiz are both submitted"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as the login identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def grades_submitted(self):
        """Check if student has submitted their grades."""
        return self.student_grades.exists()

    @property
    def quiz_submitted(self):
        """Check if student has completed the RIASEC quiz."""
        return self.quiz_responses.exists()

    @property
    def has_results(self):
        """Check if recommendations have been generated."""
        return hasattr(self, 'career_result')
