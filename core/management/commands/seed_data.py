"""
core/management/commands/seed_data.py
Seeds all static data into the database:
  - Subjects (all 8-4-4 KCSE subjects)
  - Career Clusters (10 clusters)
  - Cluster-Subject Weights (full weight matrix)
  - RIASEC Questions (all 30)
  - Institutions (Kenyan universities, TVETs)
  - Courses (university & TVET programs)
  - Labor Market Data (from KNBS/KEPSA)

Run with: python manage.py seed_data
"""

import json
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    Subject, CareerCluster, ClusterSubjectWeight,
    RIASECQuestion, Institution, Course, CourseInstitution,
    LaborMarketData
)


class Command(BaseCommand):
    help = 'Seeds all static reference data into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting database seeding...'))
        with transaction.atomic():
            self._seed_subjects()
            self._seed_clusters()
            self._seed_weights()
            self._seed_riasec_questions()
            self._seed_institutions()
            self._seed_courses()
            self._seed_labor_market()
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

    # ── SUBJECTS ─────────────────────────────────────────────────
    def _seed_subjects(self):
        subjects = [
            # Compulsory
            ('English',              'ENG', 'Compulsory',        True),
            ('Kiswahili',            'KIS', 'Compulsory',        True),
            ('Mathematics',          'MAT', 'Compulsory',        True),
            # Sciences
            ('Biology',              'BIO', 'Sciences',          False),
            ('Chemistry',            'CHE', 'Sciences',          False),
            ('Physics',              'PHY', 'Sciences',          False),
            # Humanities
            ('History & Government', 'HIS', 'Humanities',        False),
            ('Geography',            'GEO', 'Humanities',        False),
            ('Christian Religious Education', 'CRE', 'Humanities', False),
            ('Islamic Religious Education',   'IRE', 'Humanities', False),
            # Technical/Applied
            ('Agriculture',          'AGR', 'Technical/Applied', False),
            ('Home Science',         'HOM', 'Technical/Applied', False),
            ('Art & Design',         'ART', 'Technical/Applied', False),
            ('Computer Studies',     'COM', 'Technical/Applied', False),
            ('Business Studies',     'BUS', 'Technical/Applied', False),
            ('Aviation Technology',  'AVT', 'Technical/Applied', False),
            # Languages
            ('French',               'FRE', 'Languages',         False),
            ('German',               'GER', 'Languages',         False),
            ('Arabic',               'ARA', 'Languages',         False),
            # Creative
            ('Music',                'MUS', 'Creative',          False),
            ('Drawing & Design',     'DRW', 'Creative',          False),
        ]
        count = 0
        for name, code, group, compulsory in subjects:
            _, created = Subject.objects.get_or_create(
                code=code,
                defaults={'name': name, 'subject_group': group, 'is_compulsory': compulsory}
            )
            if created:
                count += 1
        self.stdout.write(f'  Subjects: {count} created')

    # ── CAREER CLUSTERS ───────────────────────────────────────────
    def _seed_clusters(self):
        clusters = [
            {
                'name':             'Engineering & Technology',
                'slug':             'engineering-technology',
                'description':      'Focuses on design, construction, and operation of structures, machines, and systems. Covers civil, mechanical, electrical, and structural engineering.',
                'riasec_primary':   'R,I',
                'riasec_secondary': 'C',
                'labor_demand':     'High',
                'icon_class':       'bi-gear-fill',
                'color_class':      'primary',
                'order_position':   1,
            },
            {
                'name':             'Health & Medical Sciences',
                'slug':             'health-medical-sciences',
                'description':      'Covers medicine, nursing, pharmacy, public health, and allied health professions. High demand across Kenya driven by healthcare expansion.',
                'riasec_primary':   'I,S',
                'riasec_secondary': 'R',
                'labor_demand':     'High',
                'icon_class':       'bi-heart-pulse-fill',
                'color_class':      'danger',
                'order_position':   2,
            },
            {
                'name':             'Information & Communication Technology',
                'slug':             'information-communication-technology',
                'description':      'Covers software development, cybersecurity, data science, networking, and digital systems. Kenya\'s fastest-growing employment sector.',
                'riasec_primary':   'I,R',
                'riasec_secondary': 'C',
                'labor_demand':     'High',
                'icon_class':       'bi-cpu-fill',
                'color_class':      'info',
                'order_position':   3,
            },
            {
                'name':             'Business & Finance',
                'slug':             'business-finance',
                'description':      'Covers accounting, banking, entrepreneurship, economics, and commerce. Foundation for Kenya\'s private sector and financial services.',
                'riasec_primary':   'E,C',
                'riasec_secondary': 'S',
                'labor_demand':     'Moderate',
                'icon_class':       'bi-bar-chart-fill',
                'color_class':      'success',
                'order_position':   4,
            },
            {
                'name':             'Education & Training',
                'slug':             'education-training',
                'description':      'Covers teaching, curriculum development, educational administration, and training facilitation across all levels of Kenya\'s education system.',
                'riasec_primary':   'S,A',
                'riasec_secondary': 'E',
                'labor_demand':     'Moderate',
                'icon_class':       'bi-mortarboard-fill',
                'color_class':      'warning',
                'order_position':   5,
            },
            {
                'name':             'Creative Arts & Media',
                'slug':             'creative-arts-media',
                'description':      'Covers journalism, graphic design, film, animation, photography, and digital content creation. Growing with Kenya\'s creative economy.',
                'riasec_primary':   'A,E',
                'riasec_secondary': 'S',
                'labor_demand':     'Moderate',
                'icon_class':       'bi-palette-fill',
                'color_class':      'danger',
                'order_position':   6,
            },
            {
                'name':             'Agriculture & Environmental Sciences',
                'slug':             'agriculture-environmental',
                'description':      'Covers agronomy, food science, environmental management, forestry, and agricultural technology. Critical to Kenya\'s food security and Vision 2030.',
                'riasec_primary':   'R,I',
                'riasec_secondary': 'S',
                'labor_demand':     'High',
                'icon_class':       'bi-tree-fill',
                'color_class':      'success',
                'order_position':   7,
            },
            {
                'name':             'Law & Social Sciences',
                'slug':             'law-social-sciences',
                'description':      'Covers law, sociology, political science, criminology, and social work. Important for governance and justice systems in Kenya.',
                'riasec_primary':   'E,S',
                'riasec_secondary': 'I',
                'labor_demand':     'Saturated',
                'icon_class':       'bi-balance-scale',
                'color_class':      'secondary',
                'order_position':   8,
            },
            {
                'name':             'TVET Trades & Technical Skills',
                'slug':             'tvet-trades-technical',
                'description':      'Covers electrical installation, plumbing, automotive, welding, construction, and other technical trades offered through TVET institutions.',
                'riasec_primary':   'R,C',
                'riasec_secondary': 'E',
                'labor_demand':     'High',
                'icon_class':       'bi-wrench-adjustable-fill',
                'color_class':      'warning',
                'order_position':   9,
            },
            {
                'name':             'Natural Sciences & Research',
                'slug':             'natural-sciences-research',
                'description':      'Covers mathematics, physics, chemistry, statistics, and research sciences. Provides foundation for advanced academia and scientific innovation.',
                'riasec_primary':   'I,R',
                'riasec_secondary': 'A',
                'labor_demand':     'Moderate',
                'icon_class':       'bi-atom',
                'color_class':      'info',
                'order_position':   10,
            },
        ]
        count = 0
        for data in clusters:
            _, created = CareerCluster.objects.get_or_create(
                slug=data['slug'], defaults=data
            )
            if created:
                count += 1
        self.stdout.write(f'  Career Clusters: {count} created')

    # ── CLUSTER SUBJECT WEIGHTS ───────────────────────────────────
    def _seed_weights(self):
        # Weight matrix from Phase 3, Section 3.3.2
        # Format: (cluster_slug, subject_code, weight)
        weights = [
            # Engineering & Technology
            ('engineering-technology', 'MAT', 1.00),
            ('engineering-technology', 'PHY', 0.95),
            ('engineering-technology', 'CHE', 0.80),
            ('engineering-technology', 'COM', 0.70),
            ('engineering-technology', 'ENG', 0.50),
            ('engineering-technology', 'GEO', 0.50),
            ('engineering-technology', 'DRW', 0.40),
            ('engineering-technology', 'KIS', 0.30),
            # Health & Medical Sciences
            ('health-medical-sciences', 'BIO', 1.00),
            ('health-medical-sciences', 'CHE', 0.90),
            ('health-medical-sciences', 'MAT', 0.70),
            ('health-medical-sciences', 'PHY', 0.60),
            ('health-medical-sciences', 'ENG', 0.60),
            ('health-medical-sciences', 'HOM', 0.60),
            ('health-medical-sciences', 'KIS', 0.40),
            # ICT
            ('information-communication-technology', 'MAT', 1.00),
            ('information-communication-technology', 'COM', 1.00),
            ('information-communication-technology', 'PHY', 0.80),
            ('information-communication-technology', 'ENG', 0.50),
            ('information-communication-technology', 'BUS', 0.40),
            ('information-communication-technology', 'CHE', 0.40),
            ('information-communication-technology', 'KIS', 0.30),
            # Business & Finance
            ('business-finance', 'BUS', 1.00),
            ('business-finance', 'MAT', 0.80),
            ('business-finance', 'ENG', 0.70),
            ('business-finance', 'HIS', 0.50),
            ('business-finance', 'GEO', 0.50),
            ('business-finance', 'KIS', 0.50),
            ('business-finance', 'COM', 0.60),
            # Education & Training
            ('education-training', 'ENG', 0.90),
            ('education-training', 'KIS', 0.80),
            ('education-training', 'MAT', 0.60),
            ('education-training', 'HIS', 0.70),
            ('education-training', 'BIO', 0.50),
            ('education-training', 'GEO', 0.60),
            ('education-training', 'CRE', 0.70),
            ('education-training', 'ART', 0.40),
            # Creative Arts & Media
            ('creative-arts-media', 'ART', 1.00),
            ('creative-arts-media', 'MUS', 1.00),
            ('creative-arts-media', 'ENG', 0.70),
            ('creative-arts-media', 'DRW', 0.90),
            ('creative-arts-media', 'COM', 0.50),
            ('creative-arts-media', 'KIS', 0.50),
            ('creative-arts-media', 'HIS', 0.40),
            # Agriculture & Environmental
            ('agriculture-environmental', 'AGR', 1.00),
            ('agriculture-environmental', 'BIO', 0.80),
            ('agriculture-environmental', 'CHE', 0.70),
            ('agriculture-environmental', 'GEO', 0.90),
            ('agriculture-environmental', 'MAT', 0.70),
            ('agriculture-environmental', 'PHY', 0.50),
            ('agriculture-environmental', 'ENG', 0.50),
            # Law & Social Sciences
            ('law-social-sciences', 'ENG', 1.00),
            ('law-social-sciences', 'HIS', 1.00),
            ('law-social-sciences', 'KIS', 0.70),
            ('law-social-sciences', 'GEO', 0.60),
            ('law-social-sciences', 'CRE', 0.70),
            ('law-social-sciences', 'BUS', 0.50),
            ('law-social-sciences', 'MAT', 0.40),
            # TVET Trades
            ('tvet-trades-technical', 'MAT', 0.90),
            ('tvet-trades-technical', 'PHY', 0.90),
            ('tvet-trades-technical', 'CHE', 0.60),
            ('tvet-trades-technical', 'COM', 0.60),
            ('tvet-trades-technical', 'ENG', 0.40),
            ('tvet-trades-technical', 'AGR', 0.40),
            ('tvet-trades-technical', 'DRW', 0.50),
            # Natural Sciences & Research
            ('natural-sciences-research', 'MAT', 1.00),
            ('natural-sciences-research', 'PHY', 1.00),
            ('natural-sciences-research', 'CHE', 1.00),
            ('natural-sciences-research', 'BIO', 0.90),
            ('natural-sciences-research', 'ENG', 0.60),
            ('natural-sciences-research', 'GEO', 0.70),
            ('natural-sciences-research', 'COM', 0.60),
        ]

        count = 0
        for cluster_slug, subject_code, weight in weights:
            try:
                cluster = CareerCluster.objects.get(slug=cluster_slug)
                subject = Subject.objects.get(code=subject_code)
                _, created = ClusterSubjectWeight.objects.get_or_create(
                    cluster=cluster, subject=subject,
                    defaults={'weight': weight}
                )
                if created:
                    count += 1
            except (CareerCluster.DoesNotExist, Subject.DoesNotExist) as e:
                self.stdout.write(self.style.ERROR(f'  Weight skip: {e}'))
        self.stdout.write(f'  Cluster-Subject Weights: {count} created')

    # ── RIASEC QUESTIONS ──────────────────────────────────────────
    def _seed_riasec_questions(self):
        questions = [
            # REALISTIC (R) — 5 questions
            ('R', 1, 'I enjoy fixing or building things with my hands.'),
            ('R', 2, 'I like working with tools, machines, or equipment.'),
            ('R', 3, 'I prefer outdoor or physical activities over sitting at a desk.'),
            ('R', 4, 'I enjoy physical or technical tasks more than purely social ones.'),
            ('R', 5, 'I like understanding how mechanical or electrical things work.'),
            # INVESTIGATIVE (I) — 5 questions
            ('I', 1, 'I enjoy solving complex problems or brain teasers.'),
            ('I', 2, 'I like conducting experiments or doing research.'),
            ('I', 3, 'I prefer thinking through problems carefully before acting.'),
            ('I', 4, 'I enjoy reading about science, technology, or new discoveries.'),
            ('I', 5, 'I like analyzing data or finding patterns in information.'),
            # ARTISTIC (A) — 5 questions
            ('A', 1, 'I enjoy drawing, painting, photography, or creative design.'),
            ('A', 2, 'I like writing stories, poetry, scripts, or creative content.'),
            ('A', 3, 'I enjoy music, drama, dance, or performing arts.'),
            ('A', 4, 'I prefer tasks that allow me to express myself creatively.'),
            ('A', 5, 'I like coming up with new ideas and original solutions.'),
            # SOCIAL (S) — 5 questions
            ('S', 1, 'I enjoy helping others solve their personal or academic problems.'),
            ('S', 2, 'I like teaching, tutoring, or explaining things clearly to people.'),
            ('S', 3, 'I prefer working in teams or groups rather than working alone.'),
            ('S', 4, 'I enjoy community service, volunteer work, or helping the needy.'),
            ('S', 5, 'I care deeply about other people\'s wellbeing and feelings.'),
            # ENTERPRISING (E) — 5 questions
            ('E', 1, 'I enjoy leading, organizing, or managing a group of people.'),
            ('E', 2, 'I like persuading or convincing others to adopt my ideas.'),
            ('E', 3, 'I enjoy or would enjoy selling, marketing, or promoting something.'),
            ('E', 4, 'I prefer taking calculated risks to achieve bigger goals.'),
            ('E', 5, 'I like starting new projects, initiatives, or small businesses.'),
            # CONVENTIONAL (C) — 5 questions
            ('C', 1, 'I enjoy organizing files, records, or data in a systematic way.'),
            ('C', 2, 'I prefer following clear procedures, rules, and guidelines.'),
            ('C', 3, 'I like working with numbers, accounts, budgets, or spreadsheets.'),
            ('C', 4, 'I enjoy tasks that require precision, attention to detail, and accuracy.'),
            ('C', 5, 'I prefer structured, predictable environments over chaotic ones.'),
        ]
        count = 0
        for rtype, pos, text in questions:
            _, created = RIASECQuestion.objects.get_or_create(
                riasec_type=rtype,
                order_position=pos,
                defaults={'question_text': text, 'is_active': True}
            )
            if created:
                count += 1
        self.stdout.write(f'  RIASEC Questions: {count} created')

    # ── INSTITUTIONS ──────────────────────────────────────────────
    def _seed_institutions(self):
        institutions = [
            # Public Universities
            ('University of Nairobi',            'Public University',  'Nairobi',     'https://uonbi.ac.ke'),
            ('Kenyatta University',               'Public University',  'Nairobi',     'https://ku.ac.ke'),
            ('Moi University',                    'Public University',  'Uasin Gishu', 'https://mu.ac.ke'),
            ('Jomo Kenyatta University (JKUAT)',  'Public University',  'Kiambu',      'https://jkuat.ac.ke'),
            ('Egerton University',                'Public University',  'Nakuru',      'https://egerton.ac.ke'),
            ('Maseno University',                 'Public University',  'Kisumu',      'https://maseno.ac.ke'),
            ('Dedan Kimathi University',          'Public University',  'Nyeri',       'https://dkut.ac.ke'),
            ('Technical University of Kenya',     'Public University',  'Nairobi',     'https://tukenya.ac.ke'),
            ('Masinde Muliro University',         'Public University',  'Kakamega',    'https://mmust.ac.ke'),
            ('South Eastern Kenya University',   'Public University',  'Kitui',       'https://seku.ac.ke'),
            ('Laikipia University',               'Public University',  'Laikipia',    'https://laikipia.ac.ke'),
            ('Kisii University',                  'Public University',  'Kisii',       'https://kisiiuniversity.ac.ke'),
            # Private Universities
            ('Strathmore University',             'Private University', 'Nairobi',     'https://strathmore.edu'),
            ('United States International University (USIU)', 'Private University', 'Nairobi', 'https://usiu.ac.ke'),
            ('Daystar University',                'Private University', 'Nairobi',     'https://daystar.ac.ke'),
            ('Catholic University of Eastern Africa (CUEA)', 'Private University', 'Nairobi', 'https://cuea.edu'),
            # TVETs
            ('Kenya Institute of Mass Communication (KIMC)', 'TVET', 'Nairobi', 'https://kimc.ac.ke'),
            ('Kenya Medical Training College (KMTC)', 'TVET', 'Nairobi', 'https://kmtc.ac.ke'),
            ('Nairobi Technical Training Institute', 'TVET', 'Nairobi', ''),
            ('Kabete National Polytechnic',       'TVET',               'Nairobi',     ''),
            ('Kisumu Polytechnic',                'TVET',               'Kisumu',      ''),
            ('Eldoret Polytechnic',               'TVET',               'Uasin Gishu', ''),
            ('Mombasa Polytechnic University College', 'TVET',          'Mombasa',     'https://mombasa.ac.ke'),
            ('Kenya Technical Trainers College',  'TVET',               'Nairobi',     ''),
            ('Rift Valley Technical Training Institute', 'TVET',        'Nakuru',      ''),
        ]
        count = 0
        for name, itype, county, website in institutions:
            _, created = Institution.objects.get_or_create(
                name=name,
                defaults={'type': itype, 'county': county, 'website': website, 'is_active': True}
            )
            if created:
                count += 1
        self.stdout.write(f'  Institutions: {count} created')

    # ── COURSES ───────────────────────────────────────────────────
    def _seed_courses(self):
        courses_data = [
            # Engineering & Technology
            {
                'name': 'Bachelor of Science in Civil Engineering',
                'cluster_slug': 'engineering-technology', 'type': 'University',
                'duration': 5.0, 'min_pts': 62.0,
                'institutions': ['University of Nairobi', 'JKUAT', 'Dedan Kimathi University'],
            },
            {
                'name': 'Bachelor of Science in Mechanical Engineering',
                'cluster_slug': 'engineering-technology', 'type': 'University',
                'duration': 5.0, 'min_pts': 60.0,
                'institutions': ['University of Nairobi', 'Moi University', 'Dedan Kimathi University'],
            },
            {
                'name': 'Bachelor of Science in Electrical Engineering',
                'cluster_slug': 'engineering-technology', 'type': 'University',
                'duration': 5.0, 'min_pts': 60.0,
                'institutions': ['University of Nairobi', 'JKUAT', 'Technical University of Kenya'],
            },
            {
                'name': 'Diploma in Building & Civil Engineering',
                'cluster_slug': 'engineering-technology', 'type': 'TVET',
                'duration': 3.0, 'min_pts': 40.0,
                'institutions': ['Kabete National Polytechnic', 'Kisumu Polytechnic', 'Mombasa Polytechnic University College'],
            },
            # Health & Medical Sciences
            {
                'name': 'Bachelor of Medicine and Surgery (MBChB)',
                'cluster_slug': 'health-medical-sciences', 'type': 'University',
                'duration': 6.0, 'min_pts': 72.0,
                'institutions': ['University of Nairobi', 'Moi University', 'Egerton University'],
            },
            {
                'name': 'Bachelor of Science in Nursing',
                'cluster_slug': 'health-medical-sciences', 'type': 'University',
                'duration': 4.0, 'min_pts': 52.0,
                'institutions': ['Kenyatta University', 'Maseno University', 'JKUAT'],
            },
            {
                'name': 'Bachelor of Pharmacy',
                'cluster_slug': 'health-medical-sciences', 'type': 'University',
                'duration': 5.0, 'min_pts': 58.0,
                'institutions': ['University of Nairobi', 'Masinde Muliro University'],
            },
            {
                'name': 'Certificate in Clinical Medicine',
                'cluster_slug': 'health-medical-sciences', 'type': 'TVET',
                'duration': 3.0, 'min_pts': 36.0,
                'institutions': ['Kenya Medical Training College (KMTC)'],
            },
            {
                'name': 'Certificate in Nursing',
                'cluster_slug': 'health-medical-sciences', 'type': 'TVET',
                'duration': 3.0, 'min_pts': 34.0,
                'institutions': ['Kenya Medical Training College (KMTC)'],
            },
            # ICT
            {
                'name': 'Bachelor of Science in Computer Science',
                'cluster_slug': 'information-communication-technology', 'type': 'University',
                'duration': 4.0, 'min_pts': 55.0,
                'institutions': ['University of Nairobi', 'Kenyatta University', 'Strathmore University', 'JKUAT'],
            },
            {
                'name': 'Bachelor of Science in Information Technology',
                'cluster_slug': 'information-communication-technology', 'type': 'University',
                'duration': 4.0, 'min_pts': 48.0,
                'institutions': ['JKUAT', 'Moi University', 'Dedan Kimathi University', 'Technical University of Kenya'],
            },
            {
                'name': 'Bachelor of Science in Software Engineering',
                'cluster_slug': 'information-communication-technology', 'type': 'University',
                'duration': 4.0, 'min_pts': 52.0,
                'institutions': ['Strathmore University', 'USIU', 'Kenyatta University'],
            },
            {
                'name': 'Diploma in ICT',
                'cluster_slug': 'information-communication-technology', 'type': 'TVET',
                'duration': 2.0, 'min_pts': 30.0,
                'institutions': ['Nairobi Technical Training Institute', 'Rift Valley Technical Training Institute'],
            },
            # Business & Finance
            {
                'name': 'Bachelor of Commerce (BCom)',
                'cluster_slug': 'business-finance', 'type': 'University',
                'duration': 4.0, 'min_pts': 44.0,
                'institutions': ['University of Nairobi', 'Kenyatta University', 'Moi University', 'Strathmore University'],
            },
            {
                'name': 'Bachelor of Business Administration (BBA)',
                'cluster_slug': 'business-finance', 'type': 'University',
                'duration': 4.0, 'min_pts': 42.0,
                'institutions': ['USIU', 'Daystar University', 'Laikipia University'],
            },
            {
                'name': 'Diploma in Business Management',
                'cluster_slug': 'business-finance', 'type': 'TVET',
                'duration': 2.0, 'min_pts': 28.0,
                'institutions': ['Nairobi Technical Training Institute', 'Eldoret Polytechnic'],
            },
            # Education & Training
            {
                'name': 'Bachelor of Education (Arts)',
                'cluster_slug': 'education-training', 'type': 'University',
                'duration': 4.0, 'min_pts': 40.0,
                'institutions': ['Kenyatta University', 'Moi University', 'Maseno University', 'Laikipia University'],
            },
            {
                'name': 'Bachelor of Education (Science)',
                'cluster_slug': 'education-training', 'type': 'University',
                'duration': 4.0, 'min_pts': 42.0,
                'institutions': ['Kenyatta University', 'JKUAT', 'Egerton University'],
            },
            # Creative Arts & Media
            {
                'name': 'Bachelor of Arts in Journalism & Mass Communication',
                'cluster_slug': 'creative-arts-media', 'type': 'University',
                'duration': 4.0, 'min_pts': 38.0,
                'institutions': ['University of Nairobi', 'Daystar University', 'USIU'],
            },
            {
                'name': 'Diploma in Mass Communication',
                'cluster_slug': 'creative-arts-media', 'type': 'TVET',
                'duration': 2.0, 'min_pts': 28.0,
                'institutions': ['Kenya Institute of Mass Communication (KIMC)'],
            },
            {
                'name': 'Diploma in Film & TV Production',
                'cluster_slug': 'creative-arts-media', 'type': 'TVET',
                'duration': 2.0, 'min_pts': 26.0,
                'institutions': ['Kenya Institute of Mass Communication (KIMC)'],
            },
            # Agriculture & Environmental
            {
                'name': 'Bachelor of Science in Agriculture',
                'cluster_slug': 'agriculture-environmental', 'type': 'University',
                'duration': 4.0, 'min_pts': 44.0,
                'institutions': ['Egerton University', 'University of Nairobi', 'Moi University'],
            },
            {
                'name': 'Bachelor of Science in Environmental Science',
                'cluster_slug': 'agriculture-environmental', 'type': 'University',
                'duration': 4.0, 'min_pts': 40.0,
                'institutions': ['Kenyatta University', 'Maseno University', 'South Eastern Kenya University'],
            },
            {
                'name': 'Diploma in Agriculture',
                'cluster_slug': 'agriculture-environmental', 'type': 'TVET',
                'duration': 2.0, 'min_pts': 26.0,
                'institutions': ['Rift Valley Technical Training Institute', 'Kisumu Polytechnic'],
            },
            # Law & Social Sciences
            {
                'name': 'Bachelor of Laws (LLB)',
                'cluster_slug': 'law-social-sciences', 'type': 'University',
                'duration': 4.0, 'min_pts': 50.0,
                'institutions': ['University of Nairobi', 'Moi University', 'Catholic University of Eastern Africa (CUEA)'],
            },
            {
                'name': 'Bachelor of Arts in Sociology',
                'cluster_slug': 'law-social-sciences', 'type': 'University',
                'duration': 4.0, 'min_pts': 38.0,
                'institutions': ['University of Nairobi', 'Maseno University', 'Kenyatta University'],
            },
            # TVET Trades
            {
                'name': 'Certificate in Electrical Installation',
                'cluster_slug': 'tvet-trades-technical', 'type': 'TVET',
                'duration': 2.0, 'min_pts': 24.0,
                'institutions': ['Kabete National Polytechnic', 'Eldoret Polytechnic', 'Kisumu Polytechnic'],
            },
            {
                'name': 'Certificate in Automotive Engineering',
                'cluster_slug': 'tvet-trades-technical', 'type': 'TVET',
                'duration': 2.0, 'min_pts': 24.0,
                'institutions': ['Kabete National Polytechnic', 'Mombasa Polytechnic University College'],
            },
            {
                'name': 'Certificate in Plumbing & Pipe Fitting',
                'cluster_slug': 'tvet-trades-technical', 'type': 'TVET',
                'duration': 1.5, 'min_pts': 22.0,
                'institutions': ['Nairobi Technical Training Institute', 'Rift Valley Technical Training Institute'],
            },
            {
                'name': 'Diploma in Building Technology',
                'cluster_slug': 'tvet-trades-technical', 'type': 'TVET',
                'duration': 3.0, 'min_pts': 30.0,
                'institutions': ['Kenya Technical Trainers College', 'Kabete National Polytechnic'],
            },
            # Natural Sciences
            {
                'name': 'Bachelor of Science in Mathematics & Computer Science',
                'cluster_slug': 'natural-sciences-research', 'type': 'University',
                'duration': 4.0, 'min_pts': 52.0,
                'institutions': ['University of Nairobi', 'Kenyatta University', 'Maseno University'],
            },
            {
                'name': 'Bachelor of Science in Chemistry',
                'cluster_slug': 'natural-sciences-research', 'type': 'University',
                'duration': 4.0, 'min_pts': 48.0,
                'institutions': ['University of Nairobi', 'Egerton University', 'Masinde Muliro University'],
            },
            {
                'name': 'Bachelor of Science in Statistics',
                'cluster_slug': 'natural-sciences-research', 'type': 'University',
                'duration': 4.0, 'min_pts': 46.0,
                'institutions': ['University of Nairobi', 'Kenyatta University', 'JKUAT'],
            },
        ]

        count = 0
        for cd in courses_data:
            try:
                cluster = CareerCluster.objects.get(slug=cd['cluster_slug'])
                course, created = Course.objects.get_or_create(
                    name=cd['name'],
                    defaults={
                        'cluster':         cluster,
                        'course_type':     cd['type'],
                        'duration_years':  cd['duration'],
                        'min_cluster_pts': cd['min_pts'],
                        'is_active':       True,
                    }
                )
                if created:
                    count += 1
                    for inst_name in cd['institutions']:
                        try:
                            inst = Institution.objects.get(name=inst_name)
                            CourseInstitution.objects.get_or_create(
                                course=course, institution=inst
                            )
                        except Institution.DoesNotExist:
                            pass
            except CareerCluster.DoesNotExist:
                pass
        self.stdout.write(f'  Courses: {count} created')

    # ── LABOR MARKET DATA ─────────────────────────────────────────
    def _seed_labor_market(self):
        # Data sourced from KNBS Economic Survey 2023 and KEPSA skills report
        lm_data = [
            {
                'cluster_slug':   'engineering-technology',
                'demand_level':   'High',
                'salary_min':     60000,
                'salary_max':     250000,
                'employers':      json.dumps(['KenGen', 'Kenya Power', 'KURA', 'KENHA', 'NCA', 'Bamburi Cement', 'ARM Cement']),
                'growth_outlook': '20% projected growth by 2030 driven by infrastructure projects',
                'saturation_note': '',
                'skills':         'AutoCAD, Project Management, Structural Analysis, GIS, SCADA Systems',
            },
            {
                'cluster_slug':   'health-medical-sciences',
                'demand_level':   'High',
                'salary_min':     55000,
                'salary_max':     350000,
                'employers':      json.dumps(['Ministry of Health', 'Aga Khan Hospital', 'Kenyatta National Hospital', 'Nairobi Hospital', 'MP Shah', 'AMREF']),
                'growth_outlook': '25% projected growth by 2030; critical shortage of doctors and nurses nationally',
                'saturation_note': '',
                'skills':         'Clinical Diagnosis, Patient Care, Pharmacology, Public Health, Research',
            },
            {
                'cluster_slug':   'information-communication-technology',
                'demand_level':   'High',
                'salary_min':     70000,
                'salary_max':     400000,
                'employers':      json.dumps(['Safaricom', 'Microsoft Kenya', 'IBM', 'Andela', 'Cellulant', 'Jumia', 'Twiga Foods', 'M-KOPA']),
                'growth_outlook': '35% projected growth by 2030; Kenya is Africa\'s leading tech hub',
                'saturation_note': '',
                'skills':         'Python, JavaScript, Cloud Computing, Cybersecurity, Machine Learning, Data Analysis',
            },
            {
                'cluster_slug':   'business-finance',
                'demand_level':   'Moderate',
                'salary_min':     40000,
                'salary_max':     200000,
                'employers':      json.dumps(['KCB Bank', 'Equity Bank', 'Safaricom', 'Deloitte Kenya', 'PwC Kenya', 'NSE', 'CMA']),
                'growth_outlook': '10% growth projected; competitive market with many graduates',
                'saturation_note': '',
                'skills':         'Financial Analysis, Excel/ERP, CPA, Accounting, Risk Management',
            },
            {
                'cluster_slug':   'education-training',
                'demand_level':   'Moderate',
                'salary_min':     30000,
                'salary_max':     120000,
                'employers':      json.dumps(['TSC (Teachers Service Commission)', 'Private Schools', 'NGOs', 'TVET Institutions', 'Universities']),
                'growth_outlook': 'Stable demand tied to CBC implementation and TVET expansion',
                'saturation_note': '',
                'skills':         'Pedagogy, CBC Curriculum, Classroom Management, Assessment Design',
            },
            {
                'cluster_slug':   'creative-arts-media',
                'demand_level':   'Moderate',
                'salary_min':     35000,
                'salary_max':     180000,
                'employers':      json.dumps(['KBC', 'Citizen TV', 'Nation Media Group', 'Standard Media', 'Sauti Sol Studios', 'Digital Agencies']),
                'growth_outlook': '18% growth driven by digital content, social media, and creative economy',
                'saturation_note': '',
                'skills':         'Video Production, Graphic Design, Adobe Suite, Social Media, Copywriting',
            },
            {
                'cluster_slug':   'agriculture-environmental',
                'demand_level':   'High',
                'salary_min':     35000,
                'salary_max':     160000,
                'employers':      json.dumps(['Kakuzi', 'Del Monte Kenya', 'Kenya Tea Development Agency', 'KARI', 'FAO', 'World Food Programme', 'NEMA']),
                'growth_outlook': '22% growth; food security and agritech are national priorities under Vision 2030',
                'saturation_note': '',
                'skills':         'Agronomy, Soil Science, GIS, Food Processing, Environmental Impact Assessment',
            },
            {
                'cluster_slug':   'law-social-sciences',
                'demand_level':   'Saturated',
                'salary_min':     50000,
                'salary_max':     300000,
                'employers':      json.dumps(['Law Firms', 'Government Ministries', 'Judiciary', 'NGOs', 'UN Agencies', 'Corporate Legal Depts']),
                'growth_outlook': 'Slow growth; highly competitive with more graduates than available positions',
                'saturation_note': 'Law and social sciences fields are currently oversaturated in Kenya. Many graduates face long waiting periods before securing employment. Consider combining with a specialized area like technology law, human rights, or environmental law for better prospects.',
                'skills':         'Legal Research, Advocacy, Human Rights, Policy Analysis, Negotiation',
            },
            {
                'cluster_slug':   'tvet-trades-technical',
                'demand_level':   'High',
                'salary_min':     30000,
                'salary_max':     150000,
                'employers':      json.dumps(['Construction Companies', 'Kenya Power', 'KenGen', 'Manufacturing Plants', 'Motor Vehicle Garages', 'Housing Contractors']),
                'growth_outlook': '30% projected growth by 2030; critical skills shortage in technical trades nationally',
                'saturation_note': '',
                'skills':         'Electrical Wiring, Welding, Plumbing, Automotive Repair, Machine Operation',
            },
            {
                'cluster_slug':   'natural-sciences-research',
                'demand_level':   'Moderate',
                'salary_min':     45000,
                'salary_max':     180000,
                'employers':      json.dumps(['KEMRI', 'KEBS', 'KEPHIS', 'Universities', 'WHO', 'Research Institutes', 'Pharmaceutical Companies']),
                'growth_outlook': '15% growth; strong in academic and research institutions',
                'saturation_note': '',
                'skills':         'Statistical Analysis, R/Python, Lab Techniques, Scientific Writing, Data Modelling',
            },
        ]

        count = 0
        for data in lm_data:
            try:
                cluster = CareerCluster.objects.get(slug=data['cluster_slug'])
                _, created = LaborMarketData.objects.get_or_create(
                    cluster=cluster,
                    defaults={
                        'demand_level':     data['demand_level'],
                        'avg_salary_min':   data['salary_min'],
                        'avg_salary_max':   data['salary_max'],
                        'key_employers':    data['employers'],
                        'growth_outlook':   data['growth_outlook'],
                        'saturation_note':  data['saturation_note'],
                        'in_demand_skills': data['skills'],
                    }
                )
                if created:
                    count += 1
            except CareerCluster.DoesNotExist:
                pass
        self.stdout.write(f'  Labor Market Data: {count} created')
