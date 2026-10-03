"""
core/engine.py
Career Pathway Recommendation Engine

Implements the complete algorithm from Phase 3:
  1. Academic Scoring Algorithm (Section 3.3)
  2. RIASEC Interest Scoring (Section 3.4)
  3. RIASEC-to-Cluster Mapping (Section 3.5)
  4. Combined Scoring & Ranking (Section 3.6)
"""

import json
import traceback
from django.conf import settings
from .models import (
    CareerCluster, ClusterSubjectWeight, StudentGrade,
    QuizResponse, RIASECResult, LaborMarketData, CareerResult
)

# ── CONSTANTS ─────────────────────────────────────────────────────
ACADEMIC_WEIGHT    = getattr(settings, 'ACADEMIC_WEIGHT',    0.60)
INTEREST_WEIGHT    = getattr(settings, 'INTEREST_WEIGHT',    0.40)
SATURATION_PENALTY = getattr(settings, 'SATURATION_PENALTY', 5.0)
TOP_N_CLUSTERS     = getattr(settings, 'TOP_N_CLUSTERS',     3)

# RIASEC-to-Cluster affinity mapping
# Each cluster maps to RIASEC types with contribution weights that sum to 1.0
RIASEC_CLUSTER_MAP = {
    'engineering-technology':               {'R': 0.40, 'I': 0.40, 'C': 0.20},
    'health-medical-sciences':              {'I': 0.40, 'S': 0.40, 'R': 0.20},
    'information-communication-technology': {'I': 0.50, 'R': 0.30, 'C': 0.20},
    'business-finance':                     {'E': 0.40, 'C': 0.40, 'S': 0.20},
    'education-training':                   {'S': 0.50, 'A': 0.30, 'E': 0.20},
    'creative-arts-media':                  {'A': 0.50, 'E': 0.30, 'S': 0.20},
    'agriculture-environmental':            {'R': 0.40, 'I': 0.40, 'S': 0.20},
    'law-social-sciences':                  {'E': 0.40, 'S': 0.40, 'I': 0.20},
    'tvet-trades-technical':                {'R': 0.50, 'C': 0.30, 'E': 0.20},
    'natural-sciences-research':            {'I': 0.50, 'R': 0.30, 'A': 0.20},
}


# ── ALGORITHM 1: Academic Score ────────────────────────────────────
def compute_academic_scores(student):
    """
    For each career cluster, compute a normalized academic score (0-100).

    Formula:
        Academic_Score(C) = [SUM(grade_points x weight)] / [SUM(12 x weight)] x 100
    """
    student_grades = {
        sg.subject_id: sg.points
        for sg in StudentGrade.objects.filter(student=student).select_related('subject')
    }

    if not student_grades:
        return {}

    all_weights = ClusterSubjectWeight.objects.select_related('cluster', 'subject').all()

    weight_map = {}
    for cw in all_weights:
        slug = cw.cluster.slug
        if slug not in weight_map:
            weight_map[slug] = {}
        weight_map[slug][cw.subject_id] = float(cw.weight)

    academic_scores = {}

    for cluster in CareerCluster.objects.all():
        slug    = cluster.slug
        weights = weight_map.get(slug, {})

        weighted_sum  = 0.0
        max_possible  = 0.0
        matched_count = 0

        for subject_id, weight in weights.items():
            if subject_id in student_grades:
                points        = student_grades[subject_id]
                weighted_sum  += points * weight
                max_possible  += 12 * weight
                matched_count += 1

        if max_possible == 0 or matched_count == 0:
            academic_scores[slug] = 0.0
        else:
            academic_scores[slug] = round((weighted_sum / max_possible) * 100, 2)

    return academic_scores


# ── ALGORITHM 2: RIASEC Score ──────────────────────────────────────
def compute_riasec_scores(student):
    """
    Sum quiz responses per RIASEC type, normalize to 0-100.
    Max raw score per type = 5 questions x 5 points = 25
    """
    responses = QuizResponse.objects.filter(
        student=student
    ).select_related('question')

    type_raw   = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
    type_count = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}

    for resp in responses:
        rtype = resp.question.riasec_type
        type_raw[rtype]   += resp.score
        type_count[rtype] += 1

    MAX_SCORE_PER_QUESTION = 5

    riasec_scores = {}
    for rtype in ['R', 'I', 'A', 'S', 'E', 'C']:
        if type_count[rtype] == 0:
            riasec_scores[rtype] = 0.0
        else:
            # Normalise by the number of questions actually answered for this
            # type, so scores stay on 0-100 if questions are added/deactivated
            max_raw = type_count[rtype] * MAX_SCORE_PER_QUESTION
            riasec_scores[rtype] = round(
                (type_raw[rtype] / max_raw) * 100, 2
            )

    sorted_types   = sorted(riasec_scores.items(), key=lambda x: x[1], reverse=True)
    dominant_types = sorted_types[0][0] + ',' + sorted_types[1][0]

    return riasec_scores, dominant_types


# ── ALGORITHM 3: Interest Score Per Cluster ────────────────────────
def compute_interest_scores(riasec_scores):
    """
    Map normalized RIASEC scores to each career cluster using
    the affinity weights in RIASEC_CLUSTER_MAP.
    """
    interest_scores = {}

    for cluster in CareerCluster.objects.all():
        slug    = cluster.slug
        mapping = RIASEC_CLUSTER_MAP.get(slug, {})

        score = 0.0
        for riasec_type, affinity_weight in mapping.items():
            score += riasec_scores.get(riasec_type, 0.0) * affinity_weight

        interest_scores[slug] = round(score, 2)

    return interest_scores


# ── ALGORITHM 4: Combined Scoring & Ranking ────────────────────────
def generate_recommendations(student, save=True):
    """
    Master recommendation function.

    When save=False the results are computed for display only: nothing is
    written to the database (used by the results page and PDF download so
    that merely viewing results does not count as a regeneration).

    Steps:
        1. Compute academic scores per cluster
        2. Compute RIASEC scores from quiz responses
        3. Save RIASEC result to DB
        4. Compute interest scores per cluster
        5. Combine: 60% academic + 40% interest
        6. Apply saturation penalty where demand = Saturated
        7. Rank all clusters, extract top 3
        8. Fetch courses, institutions, labor market for top 3
        9. Save CareerResult to DB
       10. Return structured results dict
    """
    try:
        # ── STEP 1: Academic Scores ──────────────────────────────
        academic_scores = compute_academic_scores(student)

        if not academic_scores:
            return {
                'success': False,
                'error':   'No grades found. Please enter your KCSE grades first.'
            }

        # ── STEP 2: RIASEC Scores ────────────────────────────────
        riasec_scores, dominant_types = compute_riasec_scores(student)

        # ── STEP 3: Save RIASEC Result ───────────────────────────
        if save:
            RIASECResult.objects.update_or_create(
                student=student,
                defaults={
                    'R_score':        riasec_scores['R'],
                    'I_score':        riasec_scores['I'],
                    'A_score':        riasec_scores['A'],
                    'S_score':        riasec_scores['S'],
                    'E_score':        riasec_scores['E'],
                    'C_score':        riasec_scores['C'],
                    'dominant_types': dominant_types,
                }
            )

        # ── STEP 4: Interest Scores ──────────────────────────────
        interest_scores = compute_interest_scores(riasec_scores)

        # ── STEP 5 & 6: Combined Scores + Saturation Penalty ────
        clusters        = {c.slug: c for c in CareerCluster.objects.all()}
        combined_scores = {}
        flags           = {}

        for slug, cluster in clusters.items():
            acad  = academic_scores.get(slug, 0.0)
            inter = interest_scores.get(slug, 0.0)
            score = round((acad * ACADEMIC_WEIGHT) + (inter * INTEREST_WEIGHT), 2)

            if cluster.labor_demand == 'Saturated':
                score      = max(0, score - SATURATION_PENALTY)
                flags[slug] = 'saturated'

            combined_scores[slug] = score

        # ── STEP 7: Rank All Clusters ────────────────────────────
        ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        full_ranking = []
        for rank, (slug, score) in enumerate(ranked, start=1):
            cluster = clusters[slug]
            full_ranking.append({
                'rank':           rank,
                'slug':           slug,
                'cluster_name':   cluster.name,
                'combined_score': score,
                'academic_score': academic_scores.get(slug, 0.0),
                'interest_score': interest_scores.get(slug, 0.0),
                'labor_demand':   cluster.labor_demand,
                'flagged':        flags.get(slug, ''),
            })

        top_slugs = [item['slug'] for item in full_ranking[:TOP_N_CLUSTERS]]

        # ── STEP 8: Fetch Courses, Institutions, Labor Market ───
        top_clusters = []
        for item in full_ranking[:TOP_N_CLUSTERS]:
            slug    = item['slug']
            cluster = clusters[slug]

            courses_data = []
            for course in cluster.courses.filter(is_active=True).prefetch_related('institutions'):
                institutions = list(
                    course.institutions.filter(is_active=True).values(
                        'name', 'type', 'county', 'website'
                    )
                )
                courses_data.append({
                    'id':           course.id,
                    'name':         course.name,
                    'type':         course.course_type,
                    'duration':     float(course.duration_years),
                    'min_pts':      float(course.min_cluster_pts),
                    'description':  course.description,
                    'institutions': institutions,
                })

            labor = None
            try:
                lm    = cluster.labor_market
                labor = {
                    'demand_level':     lm.demand_level,
                    'salary_min':       lm.avg_salary_min,
                    'salary_max':       lm.avg_salary_max,
                    'employers':        lm.get_employers_list(),
                    'growth_outlook':   lm.growth_outlook,
                    'saturation_note':  lm.saturation_note,
                    'in_demand_skills': lm.in_demand_skills,
                }
            except LaborMarketData.DoesNotExist:
                pass

            top_clusters.append({
                'cluster':      cluster,
                'scores':       item,
                'courses':      courses_data,
                'labor_market': labor,
                'is_saturated': flags.get(slug) == 'saturated',
            })

        # ── STEP 9: Save CareerResult ────────────────────────────
        career_result = None
        if save:
            top_cluster_objs = [clusters[slug] for slug in top_slugs]

            # Safely get existing regeneration count BEFORE update_or_create
            existing_count = 0
            try:
                existing_obj   = CareerResult.objects.get(student=student)
                existing_count = existing_obj.regenerated_count + 1
            except CareerResult.DoesNotExist:
                existing_count = 0

            career_result, created = CareerResult.objects.update_or_create(
                student=student,
                defaults={
                    'top_cluster_1':      top_cluster_objs[0] if len(top_cluster_objs) > 0 else None,
                    'top_cluster_2':      top_cluster_objs[1] if len(top_cluster_objs) > 1 else None,
                    'top_cluster_3':      top_cluster_objs[2] if len(top_cluster_objs) > 2 else None,
                    'full_ranking_json':  json.dumps(full_ranking),
                    'top_academic_score': academic_scores.get(top_slugs[0], 0),
                    'top_interest_score': interest_scores.get(top_slugs[0], 0),
                    'top_combined_score': combined_scores.get(top_slugs[0], 0),
                    'regenerated_count':  existing_count,
                }
            )

            # Mark student profile as complete
            student.profile_complete = True
            student.save(update_fields=['profile_complete'])

        return {
            'success':        True,
            'top_clusters':   top_clusters,
            'full_ranking':   full_ranking,
            'riasec_scores':  riasec_scores,
            'dominant_types': dominant_types,
            'career_result':  career_result,
        }

    except Exception as e:
        traceback.print_exc()
        return {
            'success': False,
            'error':   f"Recommendation engine error: {str(e)}"
        }


# ── RIASEC TYPE DESCRIPTIONS ───────────────────────────────────────
RIASEC_DESCRIPTIONS = {
    'R': {
        'name':        'Realistic',
        'description': 'You enjoy working with tools, machines, and physical tasks. '
                       'You are practical, hands-on, and prefer concrete problems.',
        'icon':        'bi-tools',
        'color':       'warning',
    },
    'I': {
        'name':        'Investigative',
        'description': 'You enjoy intellectual challenges, research, and analysis. '
                       'You are curious, methodical, and love solving complex problems.',
        'icon':        'bi-search',
        'color':       'info',
    },
    'A': {
        'name':        'Artistic',
        'description': 'You are creative, expressive, and imaginative. '
                       'You enjoy art, music, writing, and original thinking.',
        'icon':        'bi-palette',
        'color':       'danger',
    },
    'S': {
        'name':        'Social',
        'description': 'You enjoy helping, teaching, and working with people. '
                       'You are empathetic, communicative, and community-minded.',
        'icon':        'bi-people',
        'color':       'success',
    },
    'E': {
        'name':        'Enterprising',
        'description': 'You enjoy leading, persuading, and managing. '
                       'You are ambitious, confident, and goal-oriented.',
        'icon':        'bi-graph-up-arrow',
        'color':       'primary',
    },
    'C': {
        'name':        'Conventional',
        'description': 'You enjoy structure, order, and precision. '
                       'You are organized, detail-oriented, and systematic.',
        'icon':        'bi-clipboard-data',
        'color':       'secondary',
    },
}