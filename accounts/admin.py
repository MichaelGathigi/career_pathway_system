"""accounts/admin.py"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import StudentUser


@admin.register(StudentUser)
class StudentUserAdmin(UserAdmin):
    list_display  = ['email', 'first_name', 'last_name', 'school_name',
                     'year_completed', 'curriculum', 'profile_complete', 'created_at']
    list_filter   = ['curriculum', 'gender', 'county', 'profile_complete', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'school_name']
    ordering      = ['-created_at']

    fieldsets = (
        ('Login Info',    {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'gender', 'phone_number')}),
        ('Academic Info', {'fields': ('school_name', 'year_completed', 'curriculum', 'county')}),
        ('Status',        {'fields': ('profile_complete', 'is_active', 'is_staff')}),
        ('Dates',         {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name',
                       'password1', 'password2'),
        }),
    )
