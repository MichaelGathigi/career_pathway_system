"""core/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/',          views.dashboard,          name='dashboard'),
    path('grades/',             views.grades_entry,       name='grades_entry'),
    path('quiz/',               views.quiz_view,          name='quiz'),
    path('generate-results/',   views.generate_results,   name='generate_results'),
    path('results/',            views.results_view,       name='results'),
    path('download-report/',    views.download_pdf_report, name='download_report'),
]
