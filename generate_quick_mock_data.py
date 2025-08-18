#!/usr/bin/env python3
"""
Quick Mock Data Generator - Generates minimal data for testing

This is a faster version that generates less data for quick testing:
- 5 teachers, 50 students
- 4 weeks of attendance data
- Essential courses only

Usage: python generate_quick_mock_data.py
"""

import sys
import os
from datetime import datetime, date, time, timedelta
import random

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import (
    db, User, Student, Course, CourseEnrollment, 
    Classroom, ClassSession, Attendance, Schedule
)

class QuickMockDataGenerator:
    def __init__(self):
        self.app = create_app()
        
    def generate_all_data(self):
        """Generate minimal mock data quickly"""
        print("Starting quick mock data generation...")
        print("=" * 40)
        
        with self.app.app_context():
            try:
                # Check if database is initialized
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
                User.query.filter(User.role != 'admin').delete()
                db.session.commit()
                
                # Generate minimal data
                print("Creating 5 teachers...")
                teachers = []
                for i in range(5):
                    teacher = User(
                        username=f'teacher{i+1:02d}',
                        email=f'teacher{i+1}@college.edu',
                        role='teacher'
                    )
                    teacher.set_password('teacher123')
                    teachers.append(teacher)
                
                db.session.add_all(teachers)
                db.session.commit()
                
                print("Creating 50 students...")
                students = []
                student_users = []
                
                for i in range(50):
                    # Create user
                    user = User(
                        username=f'student{i+1:03d}',
                        email=f'student{i+1}@college.edu',
                        role='student'
                    )
                    user.set_password('student123')
                    student_users.append(user)
                
                db.session.add_all(student_users)
                db.session.commit()
                
                # Create student profiles
                for i, user in enumerate(student_users):
                    semester = random.randint(1, 4)  # Only semesters 1-4
                    student = Student(
                        student_id=f'STU2024{i+1:03d}',
                        user_id=user.id,
                        first_name=f'Student{i+1}',
                        last_name=f'LastName{i+1}',
                        email=user.email,
                        phone=f'555-{1000+i:04d}',
                        department='Computer Science',
                        year=((semester - 1) // 2) + 1,
                        semester=semester,
                        enrollment_date=datetime.utcnow() - timedelta(days=semester * 30)
                    )
                    student.generate_nfc_tag_id()
                    students.append(student)
                
                db.session.add_all(students)
                db.session.commit()
                
                print("Creating 5 classrooms...")
                classrooms = []
                for i in range(5):
                    classroom = Classroom(
                        room_number=f'A{101+i}',
                        building='Main Building',
                        capacity=50,
                        nfc_reader_id=f'NFC{i+1:03d}ABC123',
                        is_active=True
                    )
                    classrooms.append(classroom)
                
                db.session.add_all(classrooms)
                db.session.commit()
                
                print("Creating essential courses...")
                course_data = [
                    ('CS101', 'Intro Programming', 1),
                    ('MATH101', 'Calculus I', 1),
                    ('CS201', 'Data Structures', 2),
                    ('MATH201', 'Calculus II', 2),
                    ('CS301', 'Database Systems', 3),
                    ('CS302', 'Networks', 3),
                    ('CS401', 'Operating Systems', 4),
                    ('CS402', 'Algorithms', 4),
                ]
                
                courses = []
                for code, name, semester in course_data:
                    course = Course(
                        course_code=code,
                        course_name=name,
                        description=f'Description for {name}',
                        credits=3,
                        department='Computer Science',
                        semester=semester,
                        teacher_id=random.choice(teachers).id,
                        is_active=True
                    )
                    courses.append(course)
                
                db.session.add_all(courses)
                db.session.commit()
                
                print("Creating schedules...")
                schedules = []
                time_slots = [
                    (time(9, 0), time(10, 30)),
                    (time(11, 0), time(12, 30)),
                    (time(14, 0), time(15, 30)),
                ]
                
                for i, course in enumerate(courses):
                    schedule = Schedule(
                        course_id=course.id,
                        classroom_id=classrooms[i % len(classrooms)].id,
                        day_of_week=i % 5,  # Monday to Friday
                        start_time=time_slots[i % len(time_slots)][0],
                        end_time=time_slots[i % len(time_slots)][1],
                        semester=course.semester,
                        is_active=True
                    )
                    schedules.append(schedule)
                
                db.session.add_all(schedules)
                db.session.commit()
                
                print("Creating enrollments...")
                enrollments = []
                for student in students:
                    # Enroll in courses for their semester
                    semester_courses = [c for c in courses if c.semester == student.semester]
                    for course in semester_courses[:3]:  # Max 3 courses per student
                        enrollment = CourseEnrollment(
                            student_id=student.id,
                            course_id=course.id,
                            enrollment_date=student.enrollment_date,
                            is_active=True
                        )
                        enrollments.append(enrollment)
                
                db.session.add_all(enrollments)
                db.session.commit()
                
                print("Creating 4 weeks of class sessions...")
                sessions = []
                today = date.today()
                start_date = today - timedelta(weeks=4)
                
                for schedule in schedules:
                    current_date = start_date
                    while current_date <= today:
                        if current_date.weekday() == schedule.day_of_week:
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
                
                print("Creating attendance records...")
                # Create attendance mapping
                course_students = {}
                for enrollment in enrollments:
                    if enrollment.course_id not in course_students:
                        course_students[enrollment.course_id] = []
                    course_students[enrollment.course_id].append(enrollment.student_id)
                
                attendance_records = []
                for session in sessions:
                    if session.course_id in course_students:
                        for student_id in course_students[session.course_id]:
                            if random.random() < 0.8:  # 80% attendance
                                check_in_time = datetime.combine(
                                    session.session_date, 
                                    session.start_time
                                ) + timedelta(minutes=random.randint(-5, 15))
                                
                                attendance = Attendance(
                                    student_id=student_id,
                                    class_session_id=session.id,
                                    check_in_time=check_in_time,
                                    status='present',
                                    method='nfc'
                                )
                                attendance_records.append(attendance)
                
                db.session.add_all(attendance_records)
                db.session.commit()
                
                print("=" * 40)
                print("Quick mock data generation completed!")
                print(f"Summary:")
                print(f"  - Teachers: {len(teachers)}")
                print(f"  - Students: {len(students)}")
                print(f"  - Courses: {len(courses)}")
                print(f"  - Classrooms: {len(classrooms)}")
                print(f"  - Schedules: {len(schedules)}")
                print(f"  - Enrollments: {len(enrollments)}")
                print(f"  - Class Sessions: {len(sessions)}")
                print(f"  - Attendance Records: {len(attendance_records)}")
                print("=" * 40)
                
                return True
                
            except Exception as e:
                print(f"ERROR: {str(e)}")
                db.session.rollback()
                return False

def main():
    generator = QuickMockDataGenerator()
    success = generator.generate_all_data()
    
    if success:
        print("\n✅ Quick mock data generation completed!")
        print("\nLogin credentials:")
        print("- Admin: admin/admin123")
        print("- Teachers: teacher01 to teacher05 / teacher123")
        print("- Students: student001 to student050 / student123")
    else:
        print("\n❌ Quick mock data generation failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()