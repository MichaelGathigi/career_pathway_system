"""core/admin.py — Django built-in admin panel registrations"""
from django.contrib import admin
from .models import (
    Subject, CareerCluster, ClusterSubjectWeight,
    StudentGrade, RIASECQuestion, QuizResponse, RIASECResult,
    Institution, Course, CourseInstitution,
    LaborMarketData, CareerResult
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'subject_group', 'is_compulsory']
    list_filter   = ['subject_group', 'is_compulsory']
    search_fields = ['name', 'code']


@admin.register(CareerCluster)
class CareerClusterAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'riasec_primary', 'labor_demand', 'order_position']
    list_filter   = ['labor_demand']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ClusterSubjectWeight)
class ClusterSubjectWeightAdmin(admin.ModelAdmin):
    list_display  = ['cluster', 'subject', 'weight']
    list_filter   = ['cluster']
    search_fields = ['cluster__name', 'subject__name']


@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display  = ['student', 'subject', 'grade', 'points', 'created_at']
    list_filter   = ['grade', 'subject']
    search_fields = ['student__email', 'student__first_name']


@admin.register(RIASECQuestion)
class RIASECQuestionAdmin(admin.ModelAdmin):
    list_display  = ['id', 'riasec_type', 'question_text', 'order_position', 'is_active']
    list_filter   = ['riasec_type', 'is_active']
    list_editable = ['order_position', 'is_active']


@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display  = ['student', 'question', 'score', 'answered_at']
    list_filter   = ['score']
    search_fields = ['student__email']


@admin.register(RIASECResult)
class RIASECResultAdmin(admin.ModelAdmin):
    list_display  = ['student', 'dominant_types', 'R_score', 'I_score',
                     'A_score', 'S_score', 'E_score', 'C_score', 'computed_at']
    search_fields = ['student__email', 'student__first_name']


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display  = ['name', 'type', 'county', 'is_active']
    list_filter   = ['type', 'county', 'is_active']
    search_fields = ['name', 'county']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ['name', 'cluster', 'course_type', 'duration_years',
                     'min_cluster_pts', 'is_active']
    list_filter   = ['cluster', 'course_type', 'is_active']
    search_fields = ['name']


@admin.register(LaborMarketData)
class LaborMarketDataAdmin(admin.ModelAdmin):
    list_display  = ['cluster', 'demand_level', 'avg_salary_min',
                     'avg_salary_max', 'growth_outlook', 'updated_at']
    list_filter   = ['demand_level']


@admin.register(CareerResult)
class CareerResultAdmin(admin.ModelAdmin):
    list_display  = ['student', 'top_cluster_1', 'top_cluster_2', 'top_cluster_3',
                     'top_combined_score', 'generated_at', 'report_downloaded']
    list_filter   = ['report_downloaded', 'top_cluster_1']
    search_fields = ['student__email', 'student__first_name']


# Customize admin site headers
admin.site.site_header = "Career Pathway Analysis System — Admin"
admin.site.site_title  = "CPAS Admin"
admin.site.index_title = "System Administration Panel"
