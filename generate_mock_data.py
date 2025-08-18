#!/usr/bin/env python3
"""
Mock Data Generation Script for Student Attendance Management System

This script generates comprehensive mock data for all database tables:
- Users (admin, teachers, students)
- Students (profiles with NFC tags)
- Courses (across all semesters)
- Classrooms (with NFC readers)
- Schedules (weekly class schedules)
- Course Enrollments (student-course relationships)
- Class Sessions (individual class instances)
- Attendance Records (realistic attendance patterns)

Usage:
    python generate_mock_data.py

Prerequisites:
    - Database must be initialized first: python app.py init-db
    - Admin user should be created: python app.py create-admin
"""

import sys
import os
from datetime import datetime, date, time, timedelta
import random
from faker import Faker

# Add the current directory to Python path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import (
    db, User, Student, Course, CourseEnrollment, 
    Classroom, ClassSession, Attendance, Schedule
)

# Initialize Faker for generating realistic data
fake = Faker()

class MockDataGenerator:
    def __init__(self):
        self.app = create_app()
        self.departments = [
            'Computer Science', 'Information Technology', 'Electronics Engineering',
            'Mechanical Engineering', 'Civil Engineering', 'Business Administration',
            'Mathematics', 'Physics', 'Chemistry', 'English Literature'
        ]
        
        self.course_data = {
            1: [  # Semester 1
                ('CS101', 'Introduction to Programming', 'Computer Science', 4),
                ('MATH101', 'Calculus I', 'Mathematics', 4),
                ('PHY101', 'Physics I', 'Physics', 3),
                ('ENG101', 'English Composition', 'English Literature', 3),
                ('CS102', 'Computer Fundamentals', 'Computer Science', 3),
            ],
            2: [  # Semester 2
                ('CS201', 'Data Structures', 'Computer Science', 4),
                ('MATH201', 'Calculus II', 'Mathematics', 4),
                ('PHY201', 'Physics II', 'Physics', 3),
                ('ENG201', 'Technical Writing', 'English Literature', 2),
                ('CS202', 'Object Oriented Programming', 'Computer Science', 4),
            ],
            3: [  # Semester 3
                ('CS301', 'Database Systems', 'Computer Science', 4),
                ('CS302', 'Computer Networks', 'Computer Science', 4),
                ('MATH301', 'Discrete Mathematics', 'Mathematics', 3),
                ('IT301', 'Web Development', 'Information Technology', 3),
                ('CS303', 'Software Engineering', 'Computer Science', 3),
            ],
            4: [  # Semester 4
                ('CS401', 'Operating Systems', 'Computer Science', 4),
                ('CS402', 'Algorithm Analysis', 'Computer Science', 4),
                ('IT401', 'System Administration', 'Information Technology', 3),
                ('CS403', 'Computer Graphics', 'Computer Science', 3),
                ('MATH401', 'Statistics', 'Mathematics', 3),
            ],
            5: [  # Semester 5
                ('CS501', 'Machine Learning', 'Computer Science', 4),
                ('CS502', 'Artificial Intelligence', 'Computer Science', 4),
                ('IT501', 'Cybersecurity', 'Information Technology', 3),
                ('CS503', 'Mobile App Development', 'Computer Science', 3),
                ('BA501', 'Project Management', 'Business Administration', 2),
            ],
            6: [  # Semester 6
                ('CS601', 'Advanced Database Systems', 'Computer Science', 4),
                ('CS602', 'Cloud Computing', 'Computer Science', 3),
                ('IT601', 'Network Security', 'Information Technology', 3),
                ('CS603', 'Software Testing', 'Computer Science', 3),
                ('CS604', 'Human Computer Interaction', 'Computer Science', 2),
            ],
            7: [  # Semester 7
                ('CS701', 'Capstone Project I', 'Computer Science', 4),
                ('CS702', 'Advanced AI', 'Computer Science', 3),
                ('IT701', 'Enterprise Systems', 'Information Technology', 3),
                ('CS703', 'Blockchain Technology', 'Computer Science', 3),
                ('BA701', 'Entrepreneurship', 'Business Administration', 2),
            ],
            8: [  # Semester 8
                ('CS801', 'Capstone Project II', 'Computer Science', 4),
                ('CS802', 'Advanced Software Engineering', 'Computer Science', 3),
                ('IT801', 'IT Consulting', 'Information Technology', 3),
                ('CS803', 'Research Methodology', 'Computer Science', 2),
                ('CS804', 'Professional Ethics', 'Computer Science', 2),
            ]
        }
        
        self.buildings = ['Main Building', 'Science Block', 'Engineering Block', 'IT Center', 'Library Building']
        
    def generate_users(self, num_teachers=15, num_students=200):
        """Generate teacher and student users"""
        print("Generating users...")
        
        users = []
        
        # Generate teachers
        print(f"  Creating {num_teachers} teachers...")
        for i in range(num_teachers):
            teacher = User(
                username=f'teacher{i+1:03d}',
                email=fake.email(),
                role='teacher'
            )
            teacher.set_password('teacher123')
            users.append(teacher)
            
            if (i + 1) % 5 == 0:
                print(f"    Created {i + 1}/{num_teachers} teachers")
        
        # Generate students in batches for better performance
        print(f"  Creating {num_students} students...")
        batch_size = 50
        
        for batch_start in range(0, num_students, batch_size):
            batch_end = min(batch_start + batch_size, num_students)
            batch_users = []
            
            for i in range(batch_start, batch_end):
                student_user = User(
                    username=f'student{i+1:04d}',
                    email=fake.email(),
                    role='student'
                )
                student_user.set_password('student123')
                batch_users.append(student_user)
            
            # Add and commit this batch
            db.session.add_all(batch_users)
            db.session.commit()
            users.extend(batch_users)
            
            print(f"    Created {batch_end}/{num_students} students")
        
        # Add teachers to database
        db.session.add_all(users[:num_teachers])
        db.session.commit()
        
        print(f"Created {len(users)} users ({num_teachers} teachers, {num_students} students)")
        
        return users
    
    def generate_students(self, student_users):
        """Generate student profiles"""
        print("Generating student profiles...")
        
        students = []
        
        for i, user in enumerate(student_users):
            # Distribute students across semesters (more in lower semesters)
            semester_weights = [25, 20, 15, 12, 10, 8, 6, 4]  # Higher weight for lower semesters
            semester = random.choices(range(1, 9), weights=semester_weights)[0]
            
            # Calculate enrollment date based on semester
            months_ago = (semester - 1) * 6 + random.randint(0, 5)
            enrollment_date = datetime.utcnow() - timedelta(days=months_ago * 30)
            
            student = Student(
                student_id=f'STU{2024}{i+1:04d}',
                user_id=user.id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=user.email,
                phone=fake.phone_number()[:15],
                department=random.choice(self.departments),
                year=((semester - 1) // 2) + 1,  # 2 semesters per year
                semester=semester,
                enrollment_date=enrollment_date,
                auto_progression_enabled=random.choice([True, True, True, False])  # 75% enabled
            )
            student.generate_nfc_tag_id()
            students.append(student)
        
        db.session.add_all(students)
        db.session.commit()
        print(f"Created {len(students)} student profiles")
        
        return students
    
    def generate_classrooms(self, num_classrooms=25):
        """Generate classrooms with NFC readers"""
        print("Generating classrooms...")
        
        classrooms = []
        
        for i in range(num_classrooms):
            classroom = Classroom(
                room_number=f'{random.choice(self.buildings[:3])[:1]}{random.randint(100, 599)}',
                building=random.choice(self.buildings),
                capacity=random.choice([30, 40, 50, 60, 80, 100]),
                nfc_reader_id=f'NFC{i+1:03d}{fake.uuid4()[:8].upper()}',
                is_active=True
            )
            classrooms.append(classroom)
        
        db.session.add_all(classrooms)
        db.session.commit()
        print(f"Created {len(classrooms)} classrooms")
        
        return classrooms
    
    def generate_courses(self, teachers):
        """Generate courses for all semesters"""
        print("Generating courses...")
        
        courses = []
        
        for semester, course_list in self.course_data.items():
            for course_code, course_name, department, credits in course_list:
                # Assign random teacher
                teacher = random.choice(teachers)
                
                course = Course(
                    course_code=course_code,
                    course_name=course_name,
                    description=fake.text(max_nb_chars=200),
                    credits=credits,
                    department=department,
                    semester=semester,
                    teacher_id=teacher.id,
                    is_active=True
                )
                courses.append(course)
        
        db.session.add_all(courses)
        db.session.commit()
        print(f"Created {len(courses)} courses across all semesters")
        
        return courses
    
    def generate_schedules(self, courses, classrooms):
        """Generate weekly schedules for courses"""
        print("Generating course schedules...")
        
        schedules = []
        time_slots = [
            (time(8, 0), time(9, 30)),   # 8:00-9:30
            (time(9, 45), time(11, 15)), # 9:45-11:15
            (time(11, 30), time(13, 0)), # 11:30-13:00
            (time(14, 0), time(15, 30)), # 14:00-15:30
            (time(15, 45), time(17, 15)) # 15:45-17:15
        ]
        
        used_slots = {}  # Track classroom-day-time combinations
        
        for course in courses:
            # Each course has 2-3 sessions per week
            sessions_per_week = 2 if course.credits <= 3 else 3
            days_assigned = 0
            attempts = 0
            max_attempts = 50
            
            while days_assigned < sessions_per_week and attempts < max_attempts:
                day = random.randint(0, 4)  # Monday to Friday
                start_time, end_time = random.choice(time_slots)
                classroom = random.choice(classrooms)
                
                slot_key = (classroom.id, day, start_time)
                
                if slot_key not in used_slots:
                    schedule = Schedule(
                        course_id=course.id,
                        classroom_id=classroom.id,
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time,
                        semester=course.semester,
                        is_active=True
                    )
                    schedules.append(schedule)
                    used_slots[slot_key] = True
                    days_assigned += 1
                
                attempts += 1
        
        db.session.add_all(schedules)
        db.session.commit()
        print(f"Created {len(schedules)} course schedules")
        
        return schedules
    
    def generate_enrollments(self, students, courses):
        """Generate course enrollments for students"""
        print("Generating course enrollments...")
        
        enrollments = []
        
        for student in students:
            # Get courses for student's current semester
            semester_courses = [c for c in courses if c.semester == student.semester]
            
            # Enroll in 4-6 courses per semester
            num_courses = random.randint(4, min(6, len(semester_courses)))
            selected_courses = random.sample(semester_courses, num_courses)
            
            for course in selected_courses:
                enrollment = CourseEnrollment(
                    student_id=student.id,
                    course_id=course.id,
                    enrollment_date=student.enrollment_date + timedelta(days=random.randint(0, 30)),
                    is_active=True
                )
                enrollments.append(enrollment)
        
        db.session.add_all(enrollments)
        db.session.commit()
        print(f"Created {len(enrollments)} course enrollments")
        
        return enrollments
    
    def generate_class_sessions(self, schedules, weeks_back=12):
        """Generate class sessions based on schedules"""
        print("Generating class sessions...")
        
        sessions = []
        today = date.today()
        start_date = today - timedelta(weeks=weeks_back)
        
        for schedule in schedules:
            current_date = start_date
            
            while current_date <= today:
                # Check if it's the right day of week
                if current_date.weekday() == schedule.day_of_week:
                    # Skip if it's an excluded date
                    if not schedule.is_excluded_date(current_date):
                        session = ClassSession(
                            course_id=schedule.course_id,
                            classroom_id=schedule.classroom_id,
                            session_date=current_date,
                            start_time=schedule.start_time,
                            end_time=schedule.end_time,
                            is_active=True
                        )
                        sessions.append(session)
                
                current_date += timedelta(days=1)
        
        db.session.add_all(sessions)
        db.session.commit()
        print(f"Created {len(sessions)} class sessions")
        
        return sessions
    
    def generate_attendance(self, sessions, enrollments):
        """Generate realistic attendance records"""
        print("Generating attendance records...")
        
        # Create a mapping of course_id -> enrolled students
        course_students = {}
        for enrollment in enrollments:
            if enrollment.course_id not in course_students:
                course_students[enrollment.course_id] = []
            course_students[enrollment.course_id].append(enrollment.student_id)
        
        attendance_records = []
        
        for session in sessions:
            if session.course_id in course_students:
                enrolled_students = course_students[session.course_id]
                
                for student_id in enrolled_students:
                    # 85% attendance rate with some variation
                    attendance_probability = random.uniform(0.75, 0.95)
                    
                    if random.random() < attendance_probability:
                        # Determine status
                        status_weights = [80, 15, 5]  # present, late, absent
                        status = random.choices(['present', 'late', 'absent'], weights=status_weights)[0]
                        
                        if status != 'absent':
                            # Generate check-in time (within 30 minutes of start time)
                            base_datetime = datetime.combine(session.session_date, session.start_time)
                            
                            if status == 'present':
                                check_in_offset = random.randint(-5, 10)  # 5 min early to 10 min late
                            else:  # late
                                check_in_offset = random.randint(10, 30)  # 10-30 minutes late
                            
                            check_in_time = base_datetime + timedelta(minutes=check_in_offset)
                            
                            # Generate check-out time (optional, 70% of students)
                            check_out_time = None
                            if random.random() < 0.7:
                                end_datetime = datetime.combine(session.session_date, session.end_time)
                                check_out_offset = random.randint(-10, 5)  # Usually before or at end time
                                check_out_time = end_datetime + timedelta(minutes=check_out_offset)
                            
                            # Determine method
                            method_weights = [70, 20, 10]  # nfc, temp_card, manual
                            method = random.choices(['nfc', 'temp_card', 'manual'], weights=method_weights)[0]
                            
                            attendance = Attendance(
                                student_id=student_id,
                                class_session_id=session.id,
                                check_in_time=check_in_time,
                                check_out_time=check_out_time,
                                status=status,
                                method=method,
                                notes=fake.sentence() if random.random() < 0.1 else None  # 10% have notes
                            )
                            attendance_records.append(attendance)
        
        # Batch insert for better performance
        batch_size = 1000
        for i in range(0, len(attendance_records), batch_size):
            batch = attendance_records[i:i + batch_size]
            db.session.add_all(batch)
            db.session.commit()
            print(f"Inserted attendance batch {i//batch_size + 1}/{(len(attendance_records)-1)//batch_size + 1}")
        
        print(f"Created {len(attendance_records)} attendance records")
        
        return attendance_records
    
    def generate_all_data(self):
        """Generate all mock data"""
        print("Starting mock data generation...")
        print("=" * 50)
        
        with self.app.app_context():
            try:
                # Check if database is initialized by trying to query a table
                try:
                    User.query.first()
                except Exception:
                    print("ERROR: Database not initialized. Please run 'python app.py init-db' first.")
                    return False
                
                # Clear existing data (except admin user)
                print("Clearing existing data...")
                Attendance.query.delete()
                ClassSession.query.delete()
                CourseEnrollment.query.delete()
                Schedule.query.delete()
                Course.query.delete()
                Classroom.query.delete()
                Student.query.delete()
                
                # Keep admin user, delete others
                User.query.filter(User.role != 'admin').delete()
                db.session.commit()
                
                # Generate data in order of dependencies
                users = self.generate_users(num_teachers=10, num_students=100)
                teacher_users = [u for u in users if u.role == 'teacher']
                student_users = [u for u in users if u.role == 'student']
                
                students = self.generate_students(student_users)
                classrooms = self.generate_classrooms(num_classrooms=25)
                courses = self.generate_courses(teacher_users)
                schedules = self.generate_schedules(courses, classrooms)
                enrollments = self.generate_enrollments(students, courses)
                sessions = self.generate_class_sessions(schedules, weeks_back=12)
                attendance_records = self.generate_attendance(sessions, enrollments)
                
                print("=" * 50)
                print("Mock data generation completed successfully!")
                print(f"Summary:")
                print(f"  - Users: {len(users)} (+ 1 admin)")
                print(f"  - Students: {len(students)}")
                print(f"  - Courses: {len(courses)}")
                print(f"  - Classrooms: {len(classrooms)}")
                print(f"  - Schedules: {len(schedules)}")
                print(f"  - Enrollments: {len(enrollments)}")
                print(f"  - Class Sessions: {len(sessions)}")
                print(f"  - Attendance Records: {len(attendance_records)}")
                print("=" * 50)
                
                return True
                
            except Exception as e:
                print(f"ERROR: {str(e)}")
                db.session.rollback()
                return False

def main():
    """Main function to run the mock data generation"""
    generator = MockDataGenerator()
    success = generator.generate_all_data()
    
    if success:
        print("\n✅ Mock data generation completed successfully!")
        print("\nYou can now:")
        print("1. Run the application: python app.py")
        print("2. Login with admin credentials: admin/admin123")
        print("3. Or login as any student: student0001/student123 (up to student0200)")
        print("4. Or login as any teacher: teacher001/teacher123 (up to teacher015)")
    else:
        print("\n❌ Mock data generation failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()