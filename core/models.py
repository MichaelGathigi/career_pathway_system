"""
core/models.py
All Core Database Models for the Career Pathway Analysis System.

Models implement the complete database schema from Phase 2:
  - Subject, CareerCluster, ClusterSubjectWeight
  - RIASECQuestion, QuizResponse, RIASECResult
  - Course, Institution, CourseInstitution
  - LaborMarketData
  - StudentGrade
  - CareerResult
"""

from django.db import models
from django.conf import settings
import json


# ─────────────────────────────────────────────────────────────────
# TABLE 1: Subject
# All official 8-4-4 KCSE subjects
# ─────────────────────────────────────────────────────────────────
class Subject(models.Model):
    SUBJECT_GROUP_CHOICES = [
        ('Compulsory',         'Compulsory'),
        ('Sciences',           'Sciences'),
        ('Humanities',         'Humanities'),
        ('Technical/Applied',  'Technical & Applied'),
        ('Languages',          'Languages'),
        ('Creative',           'Creative & Performing Arts'),
    ]

    name          = models.CharField(max_length=100, unique=True)
    code          = models.CharField(max_length=20,  unique=True)
    subject_group = models.CharField(max_length=30,  choices=SUBJECT_GROUP_CHOICES)
    is_compulsory = models.BooleanField(default=False)
    description   = models.TextField(blank=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['subject_group', 'name']

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────
# TABLE 2: CareerCluster
# The 10 career clusters defined in Phase 2
# ─────────────────────────────────────────────────────────────────
class CareerCluster(models.Model):
    DEMAND_CHOICES = [
        ('High',      'High Demand'),
        ('Moderate',  'Moderate Demand'),
        ('Low',       'Low Demand'),
        ('Saturated', 'Saturated / Overcrowded'),
    ]

    name             = models.CharField(max_length=100, unique=True)
    slug             = models.SlugField(max_length=100, unique=True)
    description      = models.TextField()
    riasec_primary   = models.CharField(max_length=10,
                                        help_text="Primary RIASEC types e.g. R,I")
    riasec_secondary = models.CharField(max_length=10,
                                        help_text="Secondary RIASEC type e.g. C")
    labor_demand     = models.CharField(max_length=20, choices=DEMAND_CHOICES,
                                        default='Moderate')
    icon_class       = models.CharField(max_length=60, default='bi-briefcase',
                                        help_text="Bootstrap icon class")
    color_class      = models.CharField(max_length=30, default='primary',
                                        help_text="Bootstrap color e.g. success, danger")
    order_position   = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'career_clusters'
        ordering = ['order_position', 'name']

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────
# TABLE 3: ClusterSubjectWeight
# The core of the academic scoring engine (Phase 3, Section 3.3.2)
# Maps each subject to each cluster with a relevance weight (0.0–1.0)
# ─────────────────────────────────────────────────────────────────
class ClusterSubjectWeight(models.Model):
    cluster = models.ForeignKey(
        CareerCluster, on_delete=models.CASCADE,
        related_name='subject_weights'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE,
        related_name='cluster_weights'
    )
    weight  = models.DecimalField(
        max_digits=3, decimal_places=2,
        help_text="Weight 0.00–1.00: 1.0=Critical, 0.8=Important, 0.6=Useful, 0.4=Supporting"
    )

    class Meta:
        db_table = 'cluster_subject_weights'
        unique_together = [('cluster', 'subject')]

    def __str__(self):
        return f"{self.cluster.name} | {self.subject.name} = {self.weight}"


# ─────────────────────────────────────────────────────────────────
# TABLE 4: StudentGrade
# Stores each student's KCSE grade per subject
# ─────────────────────────────────────────────────────────────────
class StudentGrade(models.Model):
    GRADE_CHOICES = [
        ('A',  'A  (12 points)'),
        ('A-', 'A- (11 points)'),
        ('B+', 'B+ (10 points)'),
        ('B',  'B  (9 points)'),
        ('B-', 'B- (8 points)'),
        ('C+', 'C+ (7 points)'),
        ('C',  'C  (6 points)'),
        ('C-', 'C- (5 points)'),
        ('D+', 'D+ (4 points)'),
        ('D',  'D  (3 points)'),
        ('D-', 'D- (2 points)'),
        ('E',  'E  (1 point)'),
    ]

    # Official 8-4-4 grade-to-points mapping (Phase 3, Section 3.1)
    GRADE_POINTS = {
        'A': 12, 'A-': 11, 'B+': 10, 'B': 9,
        'B-': 8, 'C+': 7,  'C': 6,   'C-': 5,
        'D+': 4, 'D': 3,   'D-': 2,  'E': 1,
    }

    student    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='student_grades'
    )
    subject    = models.ForeignKey(
        Subject, on_delete=models.CASCADE,
        related_name='student_grades'
    )
    grade      = models.CharField(max_length=3, choices=GRADE_CHOICES)
    points     = models.PositiveSmallIntegerField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_grades'
        unique_together = [('student', 'subject')]

    def save(self, *args, **kwargs):
        # Auto-compute points from grade on save
        self.points = self.GRADE_POINTS.get(self.grade, 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.get_full_name()} | {self.subject.name}: {self.grade}"


# ─────────────────────────────────────────────────────────────────
# TABLE 5: RIASECQuestion
# The 30 standardized interest questions (Phase 3, Section 3.4.1)
# ─────────────────────────────────────────────────────────────────
class RIASECQuestion(models.Model):
    TYPE_CHOICES = [
        ('R', 'Realistic'),
        ('I', 'Investigative'),
        ('A', 'Artistic'),
        ('S', 'Social'),
        ('E', 'Enterprising'),
        ('C', 'Conventional'),
    ]

    question_text   = models.TextField()
    riasec_type     = models.CharField(max_length=1, choices=TYPE_CHOICES)
    order_position  = models.PositiveSmallIntegerField(default=0)
    is_active       = models.BooleanField(default=True)

    class Meta:
        db_table = 'riasec_questions'
        ordering = ['riasec_type', 'order_position']

    def __str__(self):
        return f"[{self.riasec_type}] {self.question_text[:60]}..."


# ─────────────────────────────────────────────────────────────────
# TABLE 6: QuizResponse
# Each student's answer (1–5) to each RIASEC question
# ─────────────────────────────────────────────────────────────────
class QuizResponse(models.Model):
    SCORE_CHOICES = [
        (1, '1 - Strongly Disagree'),
        (2, '2 - Disagree'),
        (3, '3 - Neutral'),
        (4, '4 - Agree'),
        (5, '5 - Strongly Agree'),
    ]

    student     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='quiz_responses'
    )
    question    = models.ForeignKey(
        RIASECQuestion, on_delete=models.CASCADE,
        related_name='responses'
    )
    score       = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quiz_responses'
        unique_together = [('student', 'question')]

    def __str__(self):
        return f"{self.student.email} | Q{self.question.id}: {self.score}"


# ─────────────────────────────────────────────────────────────────
# TABLE 7: RIASECResult
# Aggregated RIASEC scores after quiz completion (one per student)
# ─────────────────────────────────────────────────────────────────
class RIASECResult(models.Model):
    student        = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='riasec_result'
    )
    R_score        = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    I_score        = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    A_score        = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    S_score        = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    E_score        = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    C_score        = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    dominant_types = models.CharField(
        max_length=10,
        help_text="Top 2 RIASEC types e.g. 'R,I'"
    )
    computed_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'riasec_results'

    def __str__(self):
        return f"{self.student.get_full_name()} | Dominant: {self.dominant_types}"

    def as_dict(self):
        return {
            'R': float(self.R_score),
            'I': float(self.I_score),
            'A': float(self.A_score),
            'S': float(self.S_score),
            'E': float(self.E_score),
            'C': float(self.C_score),
        }


# ─────────────────────────────────────────────────────────────────
# TABLE 8: Institution
# Kenyan universities, TVET colleges, private colleges
# ─────────────────────────────────────────────────────────────────
class Institution(models.Model):
    TYPE_CHOICES = [
        ('Public University',  'Public University'),
        ('Private University', 'Private University'),
        ('TVET',               'TVET College'),
        ('College',            'College / Polytechnic'),
    ]

    name      = models.CharField(max_length=200, unique=True)
    type      = models.CharField(max_length=30, choices=TYPE_CHOICES)
    county    = models.CharField(max_length=100)
    website   = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'institutions'
        ordering = ['type', 'name']

    def __str__(self):
        return f"{self.name} ({self.type})"


# ─────────────────────────────────────────────────────────────────
# TABLE 9: Course
# University and TVET courses linked to career clusters
# ─────────────────────────────────────────────────────────────────
class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ('University', 'University Degree'),
        ('TVET',       'TVET Certificate/Diploma'),
        ('College',    'College Diploma'),
    ]

    name            = models.CharField(max_length=200)
    cluster         = models.ForeignKey(
        CareerCluster, on_delete=models.CASCADE,
        related_name='courses'
    )
    course_type     = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES)
    duration_years  = models.DecimalField(max_digits=3, decimal_places=1,
                                          help_text="Duration in years e.g. 4.0")
    min_cluster_pts = models.DecimalField(max_digits=4, decimal_places=1,
                                          help_text="Minimum KUCCPS cluster points required")
    description     = models.TextField(blank=True)
    institutions    = models.ManyToManyField(
        Institution,
        through='CourseInstitution',
        related_name='courses'
    )
    is_active       = models.BooleanField(default=True)

    class Meta:
        db_table = 'courses'
        ordering = ['cluster', 'name']

    def __str__(self):
        return f"{self.name} ({self.cluster.name})"


# ─────────────────────────────────────────────────────────────────
# TABLE 10: CourseInstitution (junction table)
# Many-to-many: a course offered at multiple institutions
# ─────────────────────────────────────────────────────────────────
class CourseInstitution(models.Model):
    course      = models.ForeignKey(Course,      on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)

    class Meta:
        db_table = 'course_institutions'
        unique_together = [('course', 'institution')]

    def __str__(self):
        return f"{self.course.name} @ {self.institution.name}"


# ─────────────────────────────────────────────────────────────────
# TABLE 11: LaborMarketData
# Kenya labor market insights per career cluster
# Source: KNBS, KEPSA data (Section 2.7 of proposal)
# ─────────────────────────────────────────────────────────────────
class LaborMarketData(models.Model):
    DEMAND_CHOICES = [
        ('High',      'High Demand'),
        ('Moderate',  'Moderate Demand'),
        ('Low',       'Low Demand'),
        ('Saturated', 'Saturated'),
    ]

    cluster          = models.OneToOneField(
        CareerCluster, on_delete=models.CASCADE,
        related_name='labor_market'
    )
    demand_level     = models.CharField(max_length=20, choices=DEMAND_CHOICES)
    avg_salary_min   = models.PositiveIntegerField(
        help_text="Minimum average monthly salary in KES"
    )
    avg_salary_max   = models.PositiveIntegerField(
        help_text="Maximum average monthly salary in KES"
    )
    key_employers    = models.TextField(
        help_text="JSON array of key employers e.g. [\"Safaricom\", \"KenGen\"]"
    )
    growth_outlook   = models.CharField(max_length=200)
    saturation_note  = models.TextField(
        blank=True,
        help_text="Warning message if cluster is saturated"
    )
    in_demand_skills = models.TextField(
        blank=True,
        help_text="Key skills employers are looking for"
    )
    updated_at       = models.DateField(auto_now=True)

    class Meta:
        db_table = 'labor_market_data'

    def __str__(self):
        return f"Labor Market: {self.cluster.name}"

    def get_employers_list(self):
        try:
            return json.loads(self.key_employers)
        except Exception:
            return []


# ─────────────────────────────────────────────────────────────────
# TABLE 12: CareerResult
# Final recommendation output — one record per student
# Stores all scores and ranked clusters
# ─────────────────────────────────────────────────────────────────
class CareerResult(models.Model):
    student         = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='career_result'
    )
    top_cluster_1   = models.ForeignKey(
        CareerCluster, on_delete=models.SET_NULL, null=True,
        related_name='top_result_1'
    )
    top_cluster_2   = models.ForeignKey(
        CareerCluster, on_delete=models.SET_NULL, null=True,
        related_name='top_result_2'
    )
    top_cluster_3   = models.ForeignKey(
        CareerCluster, on_delete=models.SET_NULL, null=True,
        related_name='top_result_3'
    )
    # Store full ranking as JSON for future reference
    full_ranking_json    = models.TextField(
        help_text="JSON: all 10 clusters with their scores, sorted"
    )
    # Score breakdown for top cluster (for display)
    top_academic_score   = models.DecimalField(max_digits=5, decimal_places=2)
    top_interest_score   = models.DecimalField(max_digits=5, decimal_places=2)
    top_combined_score   = models.DecimalField(max_digits=5, decimal_places=2)
    generated_at         = models.DateTimeField(auto_now_add=True)
    report_downloaded    = models.BooleanField(default=False)
    regenerated_count    = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'career_results'

    def __str__(self):
        return f"Results: {self.student.get_full_name()} | Top: {self.top_cluster_1}"

    def get_full_ranking(self):
        try:
            return json.loads(self.full_ranking_json)
        except Exception:
            return []
