from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from app.models.user import User
from app.models.student import Student
from app.models.course import Course, CourseEnrollment
from app.models.attendance import Attendance
from app.models.classroom import ClassSession
from app.models.database import db

api = Blueprint('api', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'error': 'Administrator access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@api.route('/students', methods=['POST'])
@admin_required
def create_student():
    data = request.json
    if not all(k in data for k in ('student_id', 'email', 'first_name', 'last_name')):
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter_by(email=data['email']).first() or \
       Student.query.filter_by(student_id=data['student_id']).first():
        return jsonify({'error': 'User or student ID already exists'}), 409
    
    course_ids = data.get('courses', [])

    try:
        # Use a transaction to ensure all or nothing is committed
        with db.session.begin_nested():
            user = User(
                username=data['student_id'],
                email=data['email'],
                role='student'
            )
            user.set_password(data.get('password', 'student123'))
            db.session.add(user)
            db.session.flush()

            student = Student(
                student_id=data['student_id'],
                user_id=user.id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                phone=data.get('phone'),
                department=data.get('department'),
                year=data.get('year')
            )
            student.generate_temp_card_id()
            db.session.add(student)
            db.session.flush()

            # Create course enrollments
            if course_ids:
                for course_id in course_ids:
                    enrollment = CourseEnrollment(student_id=student.id, course_id=int(course_id))
                    db.session.add(enrollment)
        
        db.session.commit()

        return jsonify({
            'message': 'Student created and enrolled successfully',
            'student_id': student.id,
            'temp_card_id': student.temp_card_id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/students', methods=['GET'])
@admin_required
def get_students():
    students = Student.query.all()
    return jsonify([{
        'id': s.id,
        'student_id': s.student_id,
        'full_name': s.full_name,
        'email': s.email,
        'department': s.department,
        'year': s.year,
        'temp_card_id': s.temp_card_id
    } for s in students])


@api.route('/courses', methods=['POST'])
@admin_required
def create_course():
    data = request.json
    if not all(k in data for k in ('course_code', 'course_name')):
        return jsonify({'error': 'Missing required fields'}), 400

    if Course.query.filter_by(course_code=data['course_code']).first():
        return jsonify({'error': 'Course code already exists'}), 409

    try:
        course = Course(
            course_code=data['course_code'],
            course_name=data['course_name'],
            description=data.get('description'),
            credits=data.get('credits', 3),
            department=data.get('department'),
            teacher_id=data.get('teacher_id')
        )
        db.session.add(course)
        db.session.commit()

        return jsonify({
            'message': 'Course created successfully',
            'course_id': course.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/courses', methods=['GET'])
@admin_required
def get_courses():
    courses = Course.query.all()
    return jsonify([{
        'id': c.id,
        'course_code': c.course_code,
        'course_name': c.course_name,
        'department': c.department,
        'credits': c.credits,
        'teacher': c.teacher.username if c.teacher else None
    } for c in courses])

@api.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    data = request.json
    qr_data = data.get('qr_data')

    if not qr_data:
        return jsonify({'error': 'Missing qr_data parameter'}), 400

    try:
        parts = qr_data.split(':')
        if len(parts) != 3 or parts[0] != 'TEMP_CARD':
            raise ValueError("Invalid QR code format")
        temp_card_id = parts[1]
        student_id_str = parts[2]
    except (ValueError, IndexError) as e:
        return jsonify({'error': f'Invalid QR data format: {e}'}), 400

    student = Student.query.filter_by(
        student_id=student_id_str,
        temp_card_id=temp_card_id
    ).first()

    if not student:
        return jsonify({'error': 'Student not found or temporary card is invalid'}), 404

    now = datetime.utcnow()
    current_time = now.time()
    current_date = now.date()

    class_session = ClassSession.query.filter(
        ClassSession.session_date == current_date,
        ClassSession.start_time <= current_time,
        ClassSession.end_time >= current_time,
        ClassSession.is_active == True
    ).first()

    if not class_session:
        return jsonify({'error': 'No active class session found at this time'}), 404

    existing_attendance = Attendance.query.filter_by(
        student_id=student.id,
        class_session_id=class_session.id
    ).first()

    if existing_attendance:
        return jsonify({
            'message': 'Attendance already marked for this session',
            'student_name': student.full_name,
            'check_in_time': existing_attendance.check_in_time.isoformat()
        }), 200

    try:
        new_attendance = Attendance(
            student_id=student.id,
            class_session_id=class_session.id,
            check_in_time=now,
            method='temp_card'
        )
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({
            'message': 'Attendance marked successfully',
            'student_name': student.full_name,
            'course': class_session.course.course_name,
            'check_in_time': now.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
