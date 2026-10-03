"""
accounts/views.py
Authentication Views: Register, Login, Logout, Profile
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import StudentRegistrationForm, StudentLoginForm


def register_view(request):
    """
    Handle student registration.
    GET:  Display empty registration form.
    POST: Validate, save new student, log them in, redirect to grades entry.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Auto-login after successful registration
            login(request, user)
            messages.success(
                request,
                f"Welcome, {user.first_name}! Your account has been created. "
                "Start by entering your KCSE grades below."
            )
            return redirect('grades_entry')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'page_title': 'Create Your Account'
    })


def login_view(request):
    """
    Handle student login using email + password.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            # Redirect to 'next' param if it exists (e.g., from login_required)
            # Only follow local URLs to prevent open redirects
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password. Please try again.")
    else:
        form = StudentLoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'page_title': 'Sign In'
    })


@login_required
def logout_view(request):
    """Log out the current student."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('landing')


@login_required
def profile_view(request):
    """Display student profile and progress summary."""
    user = request.user
    return render(request, 'accounts/profile.html', {
        'user': user,
        'grades_submitted': user.grades_submitted,
        'quiz_submitted': user.quiz_submitted,
        'has_results': user.has_results,
        'page_title': 'My Profile'
    })
