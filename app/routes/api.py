from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import random
from app.models.user import User
from app.models.student import Student
from app.models.course import Course, CourseEnrollment
from app.models.attendance import Attendance
from app.models.classroom import Classroom, ClassSession
from app.models.schedule import Schedule
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

@api.route('/classrooms', methods=['POST'])
@admin_required
def create_classroom():
    data = request.json
    if not data or 'room_number' not in data:
        return jsonify({'error': 'Missing room number'}), 400
    
    if Classroom.query.filter_by(room_number=data['room_number']).first():
        return jsonify({'error': 'Classroom with this number already exists'}), 409

    try:
        new_classroom = Classroom(
            room_number=data['room_number'],
            building=data.get('building'),
            capacity=data.get('capacity'),
            nfc_reader_id=data.get('nfc_reader_id')
        )
        db.session.add(new_classroom)
        db.session.commit()
        return jsonify({'message': 'Classroom created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/class-sessions', methods=['POST'])
@admin_required
def create_class_session():
    data = request.json
    required_fields = ['course_id', 'classroom_id', 'session_date', 'start_time', 'end_time']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        new_session = ClassSession(
            course_id=int(data['course_id']),
            classroom_id=int(data['classroom_id']),
            session_date=datetime.strptime(data['session_date'], '%Y-%m-%d').date(),
            start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(data['end_time'], '%H:%M').time()
        )
        db.session.add(new_session)
        db.session.commit()
        return jsonify({'message': 'Class session scheduled successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


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
    semester = data.get('semester', 1)  # Default to semester 1

    try:
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
                year=data.get('year'),
                semester=semester,
                auto_progression_enabled=data.get('auto_progression_enabled', True)
            )
            student.generate_nfc_tag_id()
            db.session.add(student)
            db.session.flush()

            if course_ids:
                for course_id in course_ids:
                    enrollment = CourseEnrollment(student_id=student.id, course_id=int(course_id))
                    db.session.add(enrollment)
        
        db.session.commit()

        return jsonify({
            'message': 'Student created and enrolled successfully',
            'student_id': student.id,
            'nfc_tag_id': student.nfc_tag_id,
            'semester': student.semester
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
        'nfc_tag_id': s.nfc_tag_id
    } for s in students])


@api.route('/courses', methods=['POST'])
@admin_required
def create_course():
    data = request.json
    if not all(k in data for k in ('course_code', 'course_name', 'semester')):
        return jsonify({'error': 'Missing required fields (course_code, course_name, semester)'}), 400

    if Course.query.filter_by(course_code=data['course_code']).first():
        return jsonify({'error': 'Course code already exists'}), 409

    try:
        course = Course(
            course_code=data['course_code'],
            course_name=data['course_name'],
            description=data.get('description'),
            credits=data.get('credits', 3),
            department=data.get('department'),
            semester=data.get('semester', 1),
            teacher_id=data.get('teacher_id')
        )
        db.session.add(course)
        db.session.commit()

        return jsonify({
            'message': 'Course created successfully',
            'course_id': course.id,
            'semester': course.semester
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/courses', methods=['GET'])
@admin_required
def get_courses():
    semester = request.args.get('semester', type=int)
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    
    query = Course.query.filter_by(is_active=True)
    
    # Apply semester filter
    if semester:
        query = query.filter_by(semester=semester)
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Course.course_code.ilike(search_pattern),
                Course.course_name.ilike(search_pattern),
                Course.description.ilike(search_pattern)
            )
        )
    
    # Apply department filter
    if department:
        query = query.filter_by(department=department)
    
    courses = query.order_by(Course.semester, Course.course_name).all()
    
    courses_data = []
    for c in courses:
        # Get enrollment count
        enrollment_count = CourseEnrollment.query.filter_by(
            course_id=c.id, is_active=True
        ).count()
        
        courses_data.append({
            'id': c.id,
            'course_code': c.course_code,
            'course_name': c.course_name,
            'description': c.description,
            'department': c.department,
            'credits': c.credits,
            'semester': c.semester,
            'teacher': c.teacher.username if c.teacher else None,
            'teacher_id': c.teacher_id,
            'enrollment_count': enrollment_count,
            'created_at': c.created_at.isoformat(),
            'is_active': c.is_active
        })
    
    return jsonify(courses_data)

@api.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    """
    Marks attendance for a student based on their NFC tag and the classroom's NFC reader.
    Expects a JSON payload with 'nfc_tag_id' and 'nfc_reader_id'.
    """
    data = request.json
    nfc_tag_id = data.get('nfc_tag_id')
    nfc_reader_id = data.get('nfc_reader_id')

    if not nfc_tag_id or not nfc_reader_id:
        return jsonify({'error': 'Missing nfc_tag_id or nfc_reader_id'}), 400

    # 1. Find the student by their NFC tag
    student = Student.query.filter_by(nfc_tag_id=nfc_tag_id).first()
    if not student:
        return jsonify({'error': 'Invalid student NFC tag'}), 404

    # 2. Find the classroom by the NFC reader ID
    classroom = Classroom.query.filter_by(nfc_reader_id=nfc_reader_id).first()
    if not classroom:
        return jsonify({'error': 'Invalid classroom NFC reader ID'}), 404

    # 3. Find the active class session in this specific classroom at the current time
    now = datetime.now()
    current_time = now.time()
    current_date = now.date()

    class_session = ClassSession.query.filter(
        ClassSession.classroom_id == classroom.id,
        ClassSession.session_date == current_date,
        ClassSession.start_time <= current_time,
        ClassSession.end_time >= current_time,
        ClassSession.is_active == True
    ).first()

    if not class_session:
        return jsonify({'error': f'No active class session found in classroom {classroom.room_number} at this time'}), 404

    # 4. Verify the student is enrolled in the course for this session
    is_enrolled = CourseEnrollment.query.filter_by(
        student_id=student.id,
        course_id=class_session.course_id,
        is_active=True
    ).first()

    if not is_enrolled:
        return jsonify({'error': f'Access denied: Student {student.full_name} is not enrolled in {class_session.course.course_name}.'}), 403

    # 5. Check if attendance has already been marked
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

    # 6. Record the attendance
    try:
        new_attendance = Attendance(
            student_id=student.id,
            class_session_id=class_session.id,
            check_in_time=now,
            method='nfc_card'
        )
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({
            'message': 'Attendance marked successfully',
            'student_name': student.full_name,
            'course': class_session.course.course_name,
            'classroom': classroom.room_number,
            'check_in_time': now.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@api.route('/students/progression-eligible', methods=['GET'])
@admin_required
def get_progression_eligible_students():
    """Get students eligible for semester progression"""
    eligible_students = []
    
    for student in Student.query.all():
        if student.should_progress_semester():
            progression_info = student.get_progression_info()
            eligible_students.append({
                'id': student.id,
                'student_id': student.student_id,
                'full_name': student.full_name,
                'current_semester': student.semester,
                'suggested_semester': progression_info['suggested_semester'],
                'months_enrolled': progression_info.get('months_enrolled', 0),
                'enrollment_date': student.enrollment_date.isoformat(),
                'department': student.department
            })
    
    return jsonify(eligible_students)

@api.route('/students/<int:student_id>/progress-semester', methods=['POST'])
@admin_required
def progress_student_semester(student_id):
    """Progress a single student to the next semester"""
    data = request.json
    new_semester = data.get('semester')
    force = data.get('force', False)
    
    if not new_semester:
        return jsonify({'error': 'New semester is required'}), 400
    
    student = Student.query.get_or_404(student_id)
    
    try:
        success, message = student.progress_to_semester(new_semester, force=force)
        
        if success:
            db.session.commit()
            return jsonify({
                'message': message,
                'student_id': student.student_id,
                'old_semester': student.semester if not success else new_semester - 1,
                'new_semester': student.semester
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/students/bulk-progress', methods=['POST'])
@admin_required
def bulk_progress_students():
    """Progress multiple students to their suggested semesters"""
    data = request.json
    student_ids = data.get('student_ids', [])
    
    if not student_ids:
        return jsonify({'error': 'No student IDs provided'}), 400
    
    results = []
    errors = []
    
    try:
        for student_id in student_ids:
            student = Student.query.get(student_id)
            if not student:
                errors.append(f'Student with ID {student_id} not found')
                continue
            
            if student.should_progress_semester():
                progression_info = student.get_progression_info()
                success, message = student.progress_to_semester(
                    progression_info['suggested_semester'], 
                    force=False
                )
                
                if success:
                    results.append({
                        'student_id': student.student_id,
                        'full_name': student.full_name,
                        'old_semester': progression_info['current_semester'],
                        'new_semester': student.semester,
                        'message': message
                    })
                else:
                    errors.append(f'{student.full_name}: {message}')
            else:
                errors.append(f'{student.full_name}: Not eligible for progression')
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully progressed {len(results)} students',
            'results': results,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/students/search', methods=['GET'])
@admin_required
def search_students():
    """Search and filter students with pagination"""
    # Get query parameters
    semester = request.args.get('semester', type=int)
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'last_name')
    sort_order = request.args.get('order', 'asc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Base query
    query = Student.query
    
    # Apply filters
    if semester:
        query = query.filter(Student.semester == semester)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Student.student_id.ilike(search_pattern),
                Student.first_name.ilike(search_pattern),
                Student.last_name.ilike(search_pattern),
                Student.email.ilike(search_pattern),
                Student.department.ilike(search_pattern)
            )
        )
    
    # Apply sorting
    sort_columns = {
        'student_id': Student.student_id,
        'first_name': Student.first_name,
        'last_name': Student.last_name,
        'email': Student.email,
        'department': Student.department,
        'semester': Student.semester,
        'enrollment_date': Student.enrollment_date
    }
    
    order_column = sort_columns.get(sort_by, Student.last_name)
    if sort_order == 'desc':
        order_column = order_column.desc()
    
    # Paginate results
    pagination = query.order_by(order_column).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    students_data = []
    for student in pagination.items:
        progression_info = student.get_progression_info()
        students_data.append({
            'id': student.id,
            'student_id': student.student_id,
            'full_name': student.full_name,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'email': student.email,
            'department': student.department,
            'year': student.year,
            'semester': student.semester,
            'enrollment_date': student.enrollment_date.isoformat(),
            'nfc_tag_id': student.nfc_tag_id,
            'auto_progression_enabled': student.auto_progression_enabled,
            'progression_eligible': progression_info['eligible'],
            'suggested_semester': progression_info['suggested_semester']
        })
    
    return jsonify({
        'students': students_data,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })

@api.route('/students/semester-stats', methods=['GET'])
@admin_required
def get_semester_stats():
    """Get student count statistics by semester"""
    stats = db.session.query(
        Student.semester,
        db.func.count(Student.id).label('count')
    ).group_by(Student.semester).order_by(Student.semester).all()
    
    semester_stats = [{'semester': stat.semester, 'count': stat.count} for stat in stats]
    total_students = sum(stat['count'] for stat in semester_stats)
    
    return jsonify({
        'semester_stats': semester_stats,
        'total_students': total_students
    })

@api.route('/courses/<int:course_id>', methods=['GET'])
@admin_required
def get_course_details(course_id):
    """Get detailed course information including enrollments"""
    course = Course.query.get_or_404(course_id)
    
    # Get enrolled students
    enrollments = db.session.query(CourseEnrollment, Student).join(
        Student, CourseEnrollment.student_id == Student.id
    ).filter(
        CourseEnrollment.course_id == course_id,
        CourseEnrollment.is_active == True
    ).all()
    
    enrolled_students = []
    for enrollment, student in enrollments:
        enrolled_students.append({
            'id': student.id,
            'student_id': student.student_id,
            'full_name': student.full_name,
            'email': student.email,
            'department': student.department,
            'semester': student.semester,
            'enrollment_date': enrollment.enrollment_date.isoformat()
        })
    
    return jsonify({
        'id': course.id,
        'course_code': course.course_code,
        'course_name': course.course_name,
        'description': course.description,
        'department': course.department,
        'credits': course.credits,
        'semester': course.semester,
        'teacher': course.teacher.username if course.teacher else None,
        'teacher_id': course.teacher_id,
        'is_active': course.is_active,
        'created_at': course.created_at.isoformat(),
        'enrolled_students': enrolled_students,
        'enrollment_count': len(enrolled_students)
    })

@api.route('/courses/<int:course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    """Update course information"""
    course = Course.query.get_or_404(course_id)
    data = request.json
    
    # Check if course code is being changed and if it conflicts
    if 'course_code' in data and data['course_code'] != course.course_code:
        existing = Course.query.filter_by(course_code=data['course_code']).first()
        if existing:
            return jsonify({'error': 'Course code already exists'}), 409
    
    try:
        # Update course fields
        if 'course_code' in data:
            course.course_code = data['course_code']
        if 'course_name' in data:
            course.course_name = data['course_name']
        if 'description' in data:
            course.description = data['description']
        if 'credits' in data:
            course.credits = data['credits']
        if 'department' in data:
            course.department = data['department']
        if 'semester' in data:
            course.semester = data['semester']
        if 'teacher_id' in data:
            course.teacher_id = data['teacher_id'] if data['teacher_id'] else None
        if 'is_active' in data:
            course.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Course updated successfully',
            'course_id': course.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/courses/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    """Delete (deactivate) a course"""
    course = Course.query.get_or_404(course_id)
    
    try:
        # Instead of deleting, deactivate the course
        course.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Course deactivated successfully',
            'course_id': course.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/courses/semester-stats', methods=['GET'])
@admin_required
def get_course_semester_stats():
    """Get course count statistics by semester"""
    stats = db.session.query(
        Course.semester,
        db.func.count(Course.id).label('count')
    ).filter_by(is_active=True).group_by(Course.semester).order_by(Course.semester).all()
    
    semester_stats = [{'semester': stat.semester, 'count': stat.count} for stat in stats]
    total_courses = sum(stat['count'] for stat in semester_stats)
    
    return jsonify({
        'semester_stats': semester_stats,
        'total_courses': total_courses
    })

@api.route('/courses/departments', methods=['GET'])
@admin_required
def get_course_departments():
    """Get list of unique departments from courses"""
    departments = db.session.query(Course.department).filter(
        Course.department.isnot(None),
        Course.department != '',
        Course.is_active == True
    ).distinct().order_by(Course.department).all()
    
    return jsonify([dept[0] for dept in departments if dept[0]])

@api.route('/dashboard/data', methods=['GET'])
@admin_required
def get_dashboard_data():
    """
    API endpoint to get dashboard data for dynamic updates
    """
    from datetime import timedelta
    import random
    
    # Get basic stats
    total_students = Student.query.count()
    total_courses = Course.query.count()
    total_classrooms = Classroom.query.count()
    
    # Get today's attendance data
    today = datetime.utcnow().date()
    today_attendance_count = Attendance.query.filter(
        Attendance.check_in_time >= today
    ).count()
    
    # Calculate attendance metrics (using mock data for demonstration)
    present_today = today_attendance_count if today_attendance_count > 0 else 245
    total_expected = total_students if total_students > 0 else 268
    absent_today = max(0, total_expected - present_today)
    attendance_percentage = round((present_today / total_expected * 100) if total_expected > 0 else 0)
    
    # Mock data for attendance trends (last 30 days)
    trend_labels = []
    trend_data = []
    
    for i in range(30, 0, -1):
        date = today - timedelta(days=i)
        trend_labels.append(date.strftime('%m/%d'))
        # Generate realistic mock attendance percentages
        base_rate = 85
        variation = random.randint(-8, 12)
        trend_data.append(max(70, min(98, base_rate + variation)))
    
    # Mock recent activities
    recent_activities = [
        {
            'type': 'success',
            'icon': 'user-plus',
            'message': 'New student John Doe enrolled in Computer Science',
            'time': '2 minutes ago'
        },
        {
            'type': 'info',
            'icon': 'calendar-plus',
            'message': 'Class session scheduled for Mathematics 101',
            'time': '15 minutes ago'
        },
        {
            'type': 'warning',
            'icon': 'exclamation-triangle',
            'message': '5 students marked absent in Physics class',
            'time': '1 hour ago'
        },
        {
            'type': 'primary',
            'icon': 'chart-line',
            'message': 'Weekly attendance report generated',
            'time': '2 hours ago'
        }
    ]
    
    dashboard_data = {
        'today_date': today.strftime('%B %d, %Y'),
        'total_students': total_students if total_students > 0 else 268,
        'total_courses': total_courses if total_courses > 0 else 12,
        'total_classrooms': total_classrooms if total_classrooms > 0 else 8,
        'total_sessions_today': 8,  # This would be calculated from actual schedule data
        'today_attendance': {
            'present': present_today,
            'absent': absent_today,
            'total': total_expected
        },
        'attendance_percentage': attendance_percentage,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'recent_activities': recent_activities
    }
    
    return jsonify(dashboard_data)


# Schedule Management API Endpoints

@api.route('/schedules', methods=['GET'])
@admin_required
def get_schedules():
    """Get all schedules with filtering options"""
    semester = request.args.get('semester', type=int)
    course_id = request.args.get('course_id', type=int)
    classroom_id = request.args.get('classroom_id', type=int)
    day_of_week = request.args.get('day_of_week', type=int)
    
    query = Schedule.query.filter_by(is_active=True)
    
    # Apply filters
    if semester:
        query = query.filter_by(semester=semester)
    if course_id:
        query = query.filter_by(course_id=course_id)
    if classroom_id:
        query = query.filter_by(classroom_id=classroom_id)
    if day_of_week is not None:
        query = query.filter_by(day_of_week=day_of_week)
    
    schedules = query.order_by(Schedule.day_of_week, Schedule.start_time).all()
    
    schedules_data = []
    for schedule in schedules:
        schedules_data.append({
            'id': schedule.id,
            'course_id': schedule.course_id,
            'course_code': schedule.course.course_code,
            'course_name': schedule.course.course_name,
            'classroom_id': schedule.classroom_id,
            'classroom_name': schedule.classroom.room_number,
            'classroom_building': schedule.classroom.building,
            'day_of_week': schedule.day_of_week,
            'day_name': schedule.get_day_name(),
            'start_time': schedule.start_time.strftime('%H:%M'),
            'end_time': schedule.end_time.strftime('%H:%M'),
            'time_range': schedule.get_time_range(),
            'semester': schedule.semester,
            'exclusion_dates': schedule.exclusion_dates_list,
            'created_at': schedule.created_at.isoformat(),
            'updated_at': schedule.updated_at.isoformat()
        })
    
    return jsonify(schedules_data)

@api.route('/schedules', methods=['POST'])
@admin_required
def create_schedule():
    """Create a new recurring schedule"""
    data = request.json
    required_fields = ['course_id', 'classroom_id', 'day_of_week', 'start_time', 'end_time', 'semester']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Parse time strings
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # Create new schedule
        schedule = Schedule(
            course_id=int(data['course_id']),
            classroom_id=int(data['classroom_id']),
            day_of_week=int(data['day_of_week']),
            start_time=start_time,
            end_time=end_time,
            semester=int(data['semester'])
        )
        
        # Set exclusion dates if provided
        if 'exclusion_dates' in data and data['exclusion_dates']:
            schedule.exclusion_dates_list = data['exclusion_dates']
        
        # Validate the schedule
        validation_errors = schedule.validate_schedule()
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'message': 'Schedule created successfully',
            'schedule_id': schedule.id,
            'course_code': schedule.course.course_code,
            'day_name': schedule.get_day_name(),
            'time_range': schedule.get_time_range()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/schedules/<int:schedule_id>', methods=['GET'])
@admin_required
def get_schedule_details(schedule_id):
    """Get detailed information about a specific schedule"""
    schedule = Schedule.query.get_or_404(schedule_id)
    
    return jsonify({
        'id': schedule.id,
        'course_id': schedule.course_id,
        'course_code': schedule.course.course_code,
        'course_name': schedule.course.course_name,
        'classroom_id': schedule.classroom_id,
        'classroom_name': schedule.classroom.room_number,
        'classroom_building': schedule.classroom.building,
        'classroom_capacity': schedule.classroom.capacity,
        'day_of_week': schedule.day_of_week,
        'day_name': schedule.get_day_name(),
        'start_time': schedule.start_time.strftime('%H:%M'),
        'end_time': schedule.end_time.strftime('%H:%M'),
        'time_range': schedule.get_time_range(),
        'semester': schedule.semester,
        'exclusion_dates': schedule.exclusion_dates_list,
        'is_active': schedule.is_active,
        'created_at': schedule.created_at.isoformat(),
        'updated_at': schedule.updated_at.isoformat()
    })

@api.route('/schedules/<int:schedule_id>', methods=['PUT'])
@admin_required
def update_schedule(schedule_id):
    """Update an existing schedule"""
    schedule = Schedule.query.get_or_404(schedule_id)
    data = request.json
    
    try:
        # Update fields if provided
        if 'course_id' in data:
            schedule.course_id = int(data['course_id'])
        if 'classroom_id' in data:
            schedule.classroom_id = int(data['classroom_id'])
        if 'day_of_week' in data:
            schedule.day_of_week = int(data['day_of_week'])
        if 'start_time' in data:
            schedule.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            schedule.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        if 'semester' in data:
            schedule.semester = int(data['semester'])
        if 'exclusion_dates' in data:
            schedule.exclusion_dates_list = data['exclusion_dates']
        if 'is_active' in data:
            schedule.is_active = data['is_active']
        
        # Validate the updated schedule
        validation_errors = schedule.validate_schedule()
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Schedule updated successfully',
            'schedule_id': schedule.id
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@admin_required
def delete_schedule(schedule_id):
    """Delete (deactivate) a schedule"""
    schedule = Schedule.query.get_or_404(schedule_id)
    
    try:
        schedule.is_active = False
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Schedule deactivated successfully',
            'schedule_id': schedule.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/schedules/conflicts', methods=['POST'])
@admin_required
def check_schedule_conflicts():
    """Check for conflicts with a proposed schedule"""
    data = request.json
    required_fields = ['classroom_id', 'day_of_week', 'start_time', 'end_time']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        exclude_id = data.get('exclude_id')  # For updates
        
        conflicts = Schedule.find_conflicts(
            data.get('course_id'),
            int(data['classroom_id']),
            int(data['day_of_week']),
            start_time,
            end_time,
            exclude_id=exclude_id
        )
        
        conflicts_data = []
        for conflict in conflicts:
            conflicts_data.append({
                'id': conflict.id,
                'course_code': conflict.course.course_code,
                'course_name': conflict.course.course_name,
                'day_name': conflict.get_day_name(),
                'time_range': conflict.get_time_range(),
                'semester': conflict.semester
            })
        
        return jsonify({
            'has_conflicts': len(conflicts) > 0,
            'conflicts': conflicts_data
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid time format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/schedules/timetable', methods=['GET'])
@admin_required
def get_timetable():
    """Get timetable data organized by day and time"""
    semester = request.args.get('semester', type=int)
    classroom_id = request.args.get('classroom_id', type=int)
    
    query = Schedule.query.filter_by(is_active=True)
    
    if semester:
        query = query.filter_by(semester=semester)
    if classroom_id:
        query = query.filter_by(classroom_id=classroom_id)
    
    schedules = query.order_by(Schedule.day_of_week, Schedule.start_time).all()
    
    # Organize by day of week
    timetable = {i: [] for i in range(7)}  # 0=Monday to 6=Sunday
    
    for schedule in schedules:
        timetable[schedule.day_of_week].append({
            'id': schedule.id,
            'course_code': schedule.course.course_code,
            'course_name': schedule.course.course_name,
            'classroom_name': schedule.classroom.room_number,
            'start_time': schedule.start_time.strftime('%H:%M'),
            'end_time': schedule.end_time.strftime('%H:%M'),
            'time_range': schedule.get_time_range(),
            'semester': schedule.semester,
            'exclusion_dates_count': len(schedule.exclusion_dates_list)
        })
    
    # Get day names
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return jsonify({
        'timetable': timetable,
        'day_names': day_names
    })

@api.route('/schedules/bulk-delete', methods=['POST'])
@admin_required
def bulk_delete_schedules():
    """Bulk delete (deactivate) multiple schedules"""
    data = request.json
    schedule_ids = data.get('schedule_ids', [])
    
    if not schedule_ids:
        return jsonify({'error': 'No schedule IDs provided'}), 400
    
    try:
        updated_count = Schedule.query.filter(
            Schedule.id.in_(schedule_ids)
        ).update({'is_active': False, 'updated_at': datetime.utcnow()}, synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully deactivated {updated_count} schedules',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

