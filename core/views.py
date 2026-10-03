"""
core/views.py
Main System Views:
  - Landing page
  - Student dashboard
  - KCSE grade entry
  - RIASEC quiz
  - Results display
  - PDF report generation
"""

import json
import io
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.utils.text import slugify

from .models import (
    Subject, CareerCluster, RIASECQuestion, StudentGrade,
    QuizResponse, CareerResult, LaborMarketData
)
from .engine import (
    generate_recommendations, RIASEC_DESCRIPTIONS,
    compute_academic_scores, compute_riasec_scores
)
from .pdf_generator import generate_career_report_pdf


# ─────────────────────────────────────────────────────────────────
# LANDING PAGE
# ─────────────────────────────────────────────────────────────────
def landing_page(request):
    """Public landing page — system overview and call to action."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    clusters = CareerCluster.objects.all()[:6]
    return render(request, 'core/landing.html', {
        'clusters':   clusters,
        'page_title': 'Career Pathway Analysis System',
    })


# ─────────────────────────────────────────────────────────────────
# STUDENT DASHBOARD
# ─────────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    """
    Main student dashboard showing progress through the 3-step workflow:
    Step 1: Enter Grades → Step 2: Take Quiz → Step 3: View Results
    """
    user = request.user
    career_result = None
    riasec_result = None

    try:
        career_result = user.career_result
    except CareerResult.DoesNotExist:
        pass

    try:
        riasec_result = user.riasec_result
    except Exception:
        pass

    grades_count = user.student_grades.count()

    return render(request, 'core/dashboard.html', {
        'user':           user,
        'grades_count':   grades_count,
        'grades_done':    grades_count >= 7,  # minimum 7 subjects
        'quiz_done':      user.quiz_submitted,
        'results_done':   user.has_results,
        'career_result':  career_result,
        'riasec_result':  riasec_result,
        'page_title':     'My Dashboard',
    })


# ─────────────────────────────────────────────────────────────────
# GRADE ENTRY
# ─────────────────────────────────────────────────────────────────
@login_required
def grades_entry(request):
    """
    Allow student to enter their KCSE grades per subject.
    Groups subjects by category for clean UI display.
    """
    GRADE_CHOICES = [
        ('', '-- Grade --'), ('A', 'A'), ('A-', 'A-'), ('B+', 'B+'),
        ('B', 'B'), ('B-', 'B-'), ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
        ('D+', 'D+'), ('D', 'D'), ('D-', 'D-'), ('E', 'E'),
    ]

    subjects = Subject.objects.all().order_by('subject_group', 'name')

    # Group subjects by their group for display
    grouped_subjects = {}
    for subj in subjects:
        group = subj.get_subject_group_display()
        if group not in grouped_subjects:
            grouped_subjects[group] = []
        grouped_subjects[group].append(subj)

    # Existing grades for pre-population
    existing_grades = {
        sg.subject_id: sg.grade
        for sg in request.user.student_grades.all()
    }

    if request.method == 'POST':
        submitted_grades = {}
        errors = []

        for key, value in request.POST.items():
            if key.startswith('grade_') and value:
                try:
                    subject_id = int(key.replace('grade_', ''))
                    submitted_grades[subject_id] = value
                except ValueError:
                    continue

        if len(submitted_grades) < 7:
            messages.error(
                request,
                f"Please enter grades for at least 7 subjects. "
                f"You entered {len(submitted_grades)} subject(s)."
            )
        else:
            # Validate all grades are valid choices
            valid_grades = [g[0] for g in GRADE_CHOICES if g[0]]
            invalid = [g for g in submitted_grades.values() if g not in valid_grades]
            if invalid:
                messages.error(request, "Invalid grade values detected.")
            else:
                with transaction.atomic():
                    # Remove grades for subjects the student has unselected
                    request.user.student_grades.exclude(
                        subject_id__in=submitted_grades.keys()
                    ).delete()
                    for subject_id, grade in submitted_grades.items():
                        try:
                            subj = Subject.objects.get(id=subject_id)
                            StudentGrade.objects.update_or_create(
                                student=request.user,
                                subject=subj,
                                defaults={'grade': grade}
                            )
                        except Subject.DoesNotExist:
                            continue

                messages.success(
                    request,
                    f"✓ {len(submitted_grades)} subject grades saved successfully! "
                    "Now complete the Interest Quiz."
                )
                return redirect('quiz')

    return render(request, 'core/grades_entry.html', {
        'grouped_subjects': grouped_subjects,
        'existing_grades':  existing_grades,
        'grade_choices':    GRADE_CHOICES,
        'page_title':       'Step 1: Enter Your KCSE Grades',
    })


# ─────────────────────────────────────────────────────────────────
# RIASEC QUIZ
# ─────────────────────────────────────────────────────────────────
@login_required
def quiz_view(request):
    """
    Display and process the 30-question RIASEC interest quiz.
    Questions are grouped by RIASEC type for better UX.
    """
    if not request.user.grades_submitted:
        messages.warning(request, "Please enter your KCSE grades before taking the quiz.")
        return redirect('grades_entry')

    questions = RIASECQuestion.objects.filter(is_active=True).order_by('riasec_type', 'order_position')

    # Group by RIASEC type
    grouped_questions = {}
    type_names = {'R': 'Realistic', 'I': 'Investigative', 'A': 'Artistic',
                  'S': 'Social',    'E': 'Enterprising',  'C': 'Conventional'}
    for q in questions:
        if q.riasec_type not in grouped_questions:
            grouped_questions[q.riasec_type] = {
                'type_name': type_names[q.riasec_type],
                'type_code': q.riasec_type,
                'description': RIASEC_DESCRIPTIONS[q.riasec_type]['description'],
                'questions':   []
            }
        grouped_questions[q.riasec_type]['questions'].append(q)

    # Pre-fill previous answers when the student retakes the quiz
    existing_responses = {
        r.question_id: str(r.score)
        for r in request.user.quiz_responses.all()
    }

    SCORE_LABELS = {
        '1': 'Strongly Disagree',
        '2': 'Disagree',
        '3': 'Neutral',
        '4': 'Agree',
        '5': 'Strongly Agree',
    }

    if request.method == 'POST':
        responses = {}
        missing_questions = []

        for q in questions:
            key = f"q_{q.id}"
            val = request.POST.get(key)
            if not val:
                missing_questions.append(q.id)
            else:
                try:
                    score = int(val)
                    if 1 <= score <= 5:
                        responses[q.id] = score
                    else:
                        missing_questions.append(q.id)
                except ValueError:
                    missing_questions.append(q.id)

        if missing_questions:
            messages.error(
                request,
                f"Please answer all {questions.count()} questions. "
                f"{len(missing_questions)} question(s) are unanswered."
            )
        else:
            with transaction.atomic():
                for q_id, score in responses.items():
                    QuizResponse.objects.update_or_create(
                        student=request.user,
                        question_id=q_id,
                        defaults={'score': score}
                    )

            messages.success(
                request,
                "✓ Quiz completed! Generating your personalized career recommendations..."
            )
            return redirect('generate_results')

    return render(request, 'core/quiz.html', {
        'grouped_questions': grouped_questions,
        'existing_responses': existing_responses,
        'score_labels':      SCORE_LABELS,
        'total_questions':   questions.count(),
        'page_title':        'Step 2: Interest & Personality Quiz',
    })


# ─────────────────────────────────────────────────────────────────
# GENERATE RESULTS (runs the engine)
# ─────────────────────────────────────────────────────────────────
@login_required
def generate_results(request):
    """
    Trigger the recommendation engine and redirect to results page.
    This is a processing view — no template, just logic then redirect.
    """
    if not request.user.grades_submitted:
        messages.error(request, "Please enter your grades first.")
        return redirect('grades_entry')

    if not request.user.quiz_responses.exists():
        messages.error(request, "Please complete the quiz first.")
        return redirect('quiz')

    result = generate_recommendations(request.user)

    if result['success']:
        messages.success(request, "✓ Your career pathway analysis is ready!")
        return redirect('results')
    else:
        messages.error(request, f"Error generating results: {result.get('error', 'Unknown error')}")
        return redirect('dashboard')


# ─────────────────────────────────────────────────────────────────
# RESULTS DISPLAY
# ─────────────────────────────────────────────────────────────────
@login_required
def results_view(request):
    """
    Display personalized career pathway recommendations.
    Shows top 3 clusters with courses, institutions, and labor market data.
    """
    user = request.user

    if not user.has_results:
        if user.grades_submitted and user.quiz_submitted:
            return redirect('generate_results')
        elif not user.grades_submitted:
            messages.info(request, "Start by entering your KCSE grades.")
            return redirect('grades_entry')
        else:
            messages.info(request, "Complete the interest quiz to get your results.")
            return redirect('quiz')

    career_result = user.career_result

    # Re-compute (without saving) to get full structured data for display
    result = generate_recommendations(user, save=False)

    if not result['success']:
        messages.error(request, "Error loading results. Please try again.")
        return redirect('dashboard')

    riasec_scores   = result['riasec_scores']
    dominant_types  = result['dominant_types'].split(',')

    # Build RIASEC chart data (for Chart.js radar chart)
    riasec_labels = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
    riasec_data   = [
        riasec_scores['R'], riasec_scores['I'], riasec_scores['A'],
        riasec_scores['S'], riasec_scores['E'], riasec_scores['C']
    ]

    dominant_descriptions = [
        RIASEC_DESCRIPTIONS.get(t, {}) for t in dominant_types
    ]

    return render(request, 'core/results.html', {
        'user':                  user,
        'career_result':         career_result,
        'top_clusters':          result['top_clusters'],
        'full_ranking':          result['full_ranking'],
        'riasec_scores':         riasec_scores,
        'riasec_labels_json':    json.dumps(riasec_labels),
        'riasec_data_json':      json.dumps(riasec_data),
        'dominant_types':        dominant_types,
        'dominant_descriptions': dominant_descriptions,
        'riasec_descriptions':   RIASEC_DESCRIPTIONS,
        'page_title':            'Your Career Pathway Analysis',
    })


# ─────────────────────────────────────────────────────────────────
# PDF REPORT GENERATION
# ─────────────────────────────────────────────────────────────────
@login_required
def download_pdf_report(request):
    """
    Generate and download personalized career pathway PDF report.
    Uses ReportLab to create a professional PDF (Phase 2, UC-05).
    """
    user = request.user

    if not user.has_results:
        messages.error(request, "No results found. Please complete the analysis first.")
        return redirect('dashboard')

    # Re-compute (without saving) to get full data for PDF
    result = generate_recommendations(user, save=False)

    if not result['success']:
        messages.error(request, "Error generating report.")
        return redirect('results')

    # Generate PDF
    pdf_buffer = generate_career_report_pdf(user, result)

    # Mark as downloaded
    career_result = user.career_result
    career_result.report_downloaded = True
    career_result.save(update_fields=['report_downloaded'])

    # Serve as downloadable file
    safe_name = slugify(f"{user.first_name} {user.last_name}").replace('-', '_') or 'student'
    filename = f"career_pathway_report_{safe_name}.pdf"
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
