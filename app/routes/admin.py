from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import qrcode
import base64
import random
from io import BytesIO
from app.models.user import User
from app.models.student import Student
from app.models.course import Course, CourseEnrollment
from app.models.classroom import Classroom, ClassSession
from app.models.attendance import Attendance
from app.models.schedule import Schedule
from app.models.database import db

admin = Blueprint('admin', __name__)

@admin.before_request
@login_required
def require_admin():
    if current_user.role != 'admin':
        flash('Access denied: You must be an admin to view this page.', 'danger')
        return redirect(url_for('auth.index'))

@admin.route('/dashboard')
def dashboard():
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
    # In a real implementation, this would query actual attendance records
    present_today = today_attendance_count if today_attendance_count > 0 else 245
    total_expected = total_students if total_students > 0 else 268
    absent_today = max(0, total_expected - present_today)
    attendance_percentage = round((present_today / total_expected * 100) if total_expected > 0 else 0)
    
    # Mock data for attendance trends (last 30 days)
    # In production, this would be calculated from actual attendance records
    trend_labels = []
    trend_data = []
    
    for i in range(30, 0, -1):
        date = today - timedelta(days=i)
        trend_labels.append(date.strftime('%m/%d'))
        # Generate realistic mock attendance percentages
        import random
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
        },
        {
            'type': 'success',
            'icon': 'check-circle',
            'message': 'Attendance marked for 45 students in CS101',
            'time': '3 hours ago'
        }
    ]
    
    # Get total sessions today (mock data)
    total_sessions_today = 8  # This would be calculated from actual schedule data
    
    dashboard_data = {
        'today_date': today.strftime('%B %d, %Y'),
        'total_students': total_students if total_students > 0 else 268,
        'total_courses': total_courses if total_courses > 0 else 12,
        'total_classrooms': total_classrooms if total_classrooms > 0 else 8,
        'total_sessions_today': total_sessions_today,
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
    
    return render_template('admin_dashboard.html', dashboard_data=dashboard_data)

@admin.route('/manage-students')
def manage_students():
    # Get filter parameters
    semester_filter = request.args.get('semester', type=int)
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'last_name')
    sort_order = request.args.get('order', 'asc')
    
    # Base query
    query = Student.query
    
    # Apply semester filter
    if semester_filter:
        query = query.filter(Student.semester == semester_filter)
    
    # Apply search filter
    if search_query:
        search_pattern = f"%{search_query}%"
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
    if sort_by == 'student_id':
        order_column = Student.student_id
    elif sort_by == 'first_name':
        order_column = Student.first_name
    elif sort_by == 'email':
        order_column = Student.email
    elif sort_by == 'department':
        order_column = Student.department
    elif sort_by == 'semester':
        order_column = Student.semester
    elif sort_by == 'enrollment_date':
        order_column = Student.enrollment_date
    else:  # default to last_name
        order_column = Student.last_name
    
    if sort_order == 'desc':
        order_column = order_column.desc()
    
    students = query.order_by(order_column).all()
    
    # Get semester statistics for filter dropdown
    semester_stats = db.session.query(
        Student.semester,
        db.func.count(Student.id).label('count')
    ).group_by(Student.semester).order_by(Student.semester).all()
    
    # Get students eligible for progression
    eligible_students = []
    for student in Student.query.all():
        if student.should_progress_semester():
            progression_info = student.get_progression_info()
            eligible_students.append({
                'student': student,
                'progression_info': progression_info
            })
    
    courses = Course.query.order_by(Course.course_name).all()
    
    return render_template('manage_students.html', 
                         students=students, 
                         courses=courses,
                         semester_stats=semester_stats,
                         eligible_students=eligible_students,
                         current_filters={
                             'semester': semester_filter,
                             'search': search_query,
                             'sort': sort_by,
                             'order': sort_order
                         })

@admin.route('/manage-courses')
def manage_courses():
    # Get filter parameters
    semester_filter = request.args.get('semester', type=int)
    search_query = request.args.get('search', '').strip()
    department_filter = request.args.get('department', '').strip()
    
    # Base query for active courses
    query = Course.query.filter_by(is_active=True)
    
    # Apply filters
    if semester_filter:
        query = query.filter_by(semester=semester_filter)
    
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Course.course_code.ilike(search_pattern),
                Course.course_name.ilike(search_pattern),
                Course.description.ilike(search_pattern)
            )
        )
    
    if department_filter:
        query = query.filter_by(department=department_filter)
    
    courses = query.order_by(Course.semester, Course.course_name).all()
    
    # Get semester statistics
    semester_stats = db.session.query(
        Course.semester,
        db.func.count(Course.id).label('count')
    ).filter_by(is_active=True).group_by(Course.semester).order_by(Course.semester).all()
    
    # Get unique departments
    departments = db.session.query(Course.department).filter(
        Course.department.isnot(None),
        Course.department != '',
        Course.is_active == True
    ).distinct().order_by(Course.department).all()
    department_list = [dept[0] for dept in departments if dept[0]]
    
    # Get teachers
    teachers = User.query.filter_by(role='teacher').all()
    
    # Group courses by semester for display
    courses_by_semester = {}
    for course in courses:
        semester = course.semester
        if semester not in courses_by_semester:
            courses_by_semester[semester] = []
        
        # Get enrollment count for each course
        enrollment_count = CourseEnrollment.query.filter_by(
            course_id=course.id, is_active=True
        ).count()
        
        course_data = {
            'course': course,
            'enrollment_count': enrollment_count
        }
        courses_by_semester[semester].append(course_data)
    
    return render_template('manage_courses.html', 
                         courses=courses,
                         courses_by_semester=courses_by_semester,
                         teachers=teachers,
                         semester_stats=semester_stats,
                         departments=department_list,
                         current_filters={
                             'semester': semester_filter,
                             'search': search_query,
                             'department': department_filter
                         })

@admin.route('/manage-schedule')
def manage_schedule():
    # Get filter parameters
    semester_filter = request.args.get('semester', type=int)
    classroom_filter = request.args.get('classroom', type=int)
    view_type = request.args.get('view', 'timetable')  # timetable or list
    
    # Get all data for dropdowns and forms
    classrooms = Classroom.query.filter_by(is_active=True).order_by(Classroom.room_number).all()
    courses = Course.query.filter_by(is_active=True).order_by(Course.semester, Course.course_name).all()
    
    # Get schedules with filters
    schedule_query = Schedule.query.filter_by(is_active=True)
    
    if semester_filter:
        schedule_query = schedule_query.filter_by(semester=semester_filter)
    if classroom_filter:
        schedule_query = schedule_query.filter_by(classroom_id=classroom_filter)
    
    schedules = schedule_query.order_by(Schedule.day_of_week, Schedule.start_time).all()
    
    # Get semester statistics
    semester_stats = db.session.query(
        Schedule.semester,
        db.func.count(Schedule.id).label('count')
    ).filter_by(is_active=True).group_by(Schedule.semester).order_by(Schedule.semester).all()
    
    # Organize schedules for timetable view
    timetable = {i: [] for i in range(7)}  # 0=Monday to 6=Sunday
    for schedule in schedules:
        timetable[schedule.day_of_week].append(schedule)
    
    # Get class sessions for backward compatibility
    sessions = ClassSession.query.order_by(ClassSession.session_date.desc(), ClassSession.start_time.desc()).limit(10).all()
    
    # Day names for display
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return render_template('manage_schedule.html', 
                         classrooms=classrooms, 
                         courses=courses,
                         schedules=schedules,
                         sessions=sessions,
                         timetable=timetable,
                         day_names=day_names,
                         semester_stats=semester_stats,
                         current_filters={
                             'semester': semester_filter,
                             'classroom': classroom_filter,
                             'view': view_type
                         })


@admin.route('/manage-attendance')
def attendance_records():
    # Get filter parameters
    semester_filter = request.args.get('semester', type=int)
    course_filter = request.args.get('course', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status_filter = request.args.get('status', '').strip()
    search_query = request.args.get('search', '').strip()
    view_type = request.args.get('view', 'table')  # table or calendar
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Base query with joins for filtering
    query = db.session.query(Attendance).join(Student).join(ClassSession).join(Course)
    
    # Apply filters
    if semester_filter:
        query = query.filter(Student.semester == semester_filter)
    
    if course_filter:
        query = query.filter(Course.id == course_filter)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Attendance.check_in_time) >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Attendance.check_in_time) <= to_date)
        except ValueError:
            pass
    
    if status_filter:
        query = query.filter(Attendance.status == status_filter)
    
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Student.student_id.ilike(search_pattern),
                Student.first_name.ilike(search_pattern),
                Student.last_name.ilike(search_pattern),
                Course.course_code.ilike(search_pattern),
                Course.course_name.ilike(search_pattern)
            )
        )
    
    # Order by check-in time descending
    query = query.order_by(Attendance.check_in_time.desc())
    
    # Paginate results
    records = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get filter options
    semester_stats = db.session.query(
        Student.semester,
        db.func.count(db.distinct(Attendance.id)).label('count')
    ).join(Attendance).group_by(Student.semester).order_by(Student.semester).all()
    
    courses_with_attendance = db.session.query(
        Course.id, Course.course_code, Course.course_name, Course.semester,
        db.func.count(db.distinct(Attendance.id)).label('count')
    ).select_from(Course).join(ClassSession, Course.id == ClassSession.course_id).join(
        Attendance, ClassSession.id == Attendance.class_session_id
    ).group_by(
        Course.id, Course.course_code, Course.course_name, Course.semester
    ).order_by(Course.semester, Course.course_name).all()
    
    # Get attendance statistics
    total_records = query.count()
    present_count = query.filter(Attendance.status == 'present').count()
    late_count = query.filter(Attendance.status == 'late').count()
    absent_count = query.filter(Attendance.status == 'absent').count()
    
    attendance_stats = {
        'total': total_records,
        'present': present_count,
        'late': late_count,
        'absent': absent_count,
        'present_percentage': round((present_count / total_records * 100) if total_records > 0 else 0, 1),
        'late_percentage': round((late_count / total_records * 100) if total_records > 0 else 0, 1),
        'absent_percentage': round((absent_count / total_records * 100) if total_records > 0 else 0, 1)
    }
    
    # Get calendar data if calendar view is requested
    calendar_data = []
    if view_type == 'calendar':
        # Get attendance data for calendar view (last 30 days by default)
        if not date_from:
            date_from = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.utcnow().strftime('%Y-%m-%d')
        
        calendar_query = db.session.query(
            db.func.date(Attendance.check_in_time).label('date'),
            Attendance.status,
            db.func.count(Attendance.id).label('count')
        ).filter(
            db.func.date(Attendance.check_in_time) >= datetime.strptime(date_from, '%Y-%m-%d').date(),
            db.func.date(Attendance.check_in_time) <= datetime.strptime(date_to, '%Y-%m-%d').date()
        )
        
        # Apply same filters for calendar
        if semester_filter:
            calendar_query = calendar_query.join(Student, Attendance.student_id == Student.id).filter(Student.semester == semester_filter)
        if course_filter:
            calendar_query = calendar_query.join(ClassSession, Attendance.class_session_id == ClassSession.id).join(Course, ClassSession.course_id == Course.id).filter(Course.id == course_filter)
        
        calendar_results = calendar_query.group_by(
            db.func.date(Attendance.check_in_time), Attendance.status
        ).all()
        
        # Process calendar data
        calendar_dict = {}
        for result in calendar_results:
            # Handle both date objects and string dates
            if hasattr(result.date, 'strftime'):
                date_str = result.date.strftime('%Y-%m-%d')
            else:
                date_str = str(result.date)
            
            if date_str not in calendar_dict:
                calendar_dict[date_str] = {'present': 0, 'late': 0, 'absent': 0}
            calendar_dict[date_str][result.status] = result.count
        
        calendar_data = [
            {
                'date': date,
                'present': data['present'],
                'late': data['late'],
                'absent': data['absent'],
                'total': data['present'] + data['late'] + data['absent']
            }
            for date, data in calendar_dict.items()
        ]
        calendar_data.sort(key=lambda x: x['date'])
    
    # Get all students and courses for add attendance form
    students = Student.query.order_by(Student.semester, Student.last_name).all()
    all_courses = Course.query.filter_by(is_active=True).order_by(Course.semester, Course.course_name).all()
    
    # Convert to JSON-serializable format
    students_json = [{
        'id': student.id,
        'student_id': student.student_id,
        'full_name': student.full_name,
        'semester': student.semester
    } for student in students]
    
    courses_json = [{
        'id': course.id,
        'course_code': course.course_code,
        'course_name': course.course_name,
        'semester': course.semester
    } for course in all_courses]
    
    return render_template('attendance_records.html', 
                         records=records,
                         semester_stats=semester_stats,
                         courses_with_attendance=courses_with_attendance,
                         attendance_stats=attendance_stats,
                         calendar_data=calendar_data,
                         students=students,
                         all_courses=all_courses,
                         students_json=students_json,
                         courses_json=courses_json,
                         current_filters={
                             'semester': semester_filter,
                             'course': course_filter,
                             'date_from': date_from,
                             'date_to': date_to,
                             'status': status_filter,
                             'search': search_query,
                             'view': view_type
                         })

@admin.route('/id-card/<int:student_id>')
def generate_id_card(student_id):
    student = Student.query.get_or_404(student_id)
    if not student.nfc_tag_id:
        student.generate_nfc_tag_id()
        db.session.commit()

    qr_data = f"NFC_CARD:{student.nfc_tag_id}:{student.student_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer)
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return render_template('id_card.html', student=student, qr_code=img_str)

@admin.route('/api/attendance/add', methods=['POST'])
def add_attendance():
    """Add new attendance record"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_id', 'course_id', 'date', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get student and course
        student = Student.query.get(data['student_id'])
        course = Course.query.get(data['course_id'])
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Parse date and time
        attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        check_in_time = datetime.combine(attendance_date, datetime.strptime(data.get('time', '09:00'), '%H:%M').time())
        
        # Create or find class session (simplified - in real app, this would be more complex)
        
        # Try to find existing session or create a new one
        session = ClassSession.query.filter_by(
            course_id=course.id,
            session_date=attendance_date
        ).first()
        
        if not session:
            # Create a default classroom if none exists
            classroom = Classroom.query.first()
            if not classroom:
                classroom = Classroom(
                    room_number='Default Room',
                    capacity=50,
                    building='Main Building'
                )
                db.session.add(classroom)
                db.session.flush()
            
            session = ClassSession(
                course_id=course.id,
                classroom_id=classroom.id,
                session_date=attendance_date,
                start_time=check_in_time.time(),
                end_time=(check_in_time + timedelta(hours=1)).time()
            )
            db.session.add(session)
            db.session.flush()
        
        # Check if attendance already exists
        existing_attendance = Attendance.query.filter_by(
            student_id=student.id,
            class_session_id=session.id
        ).first()
        
        if existing_attendance:
            return jsonify({'error': 'Attendance record already exists for this student and session'}), 400
        
        # Create attendance record
        attendance = Attendance(
            student_id=student.id,
            class_session_id=session.id,
            check_in_time=check_in_time,
            status=data['status'],
            method='manual',
            notes=data.get('notes', '')
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Attendance recorded for {student.full_name}',
            'attendance_id': attendance.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin.route('/api/attendance/bulk-update', methods=['POST'])
def bulk_update_attendance():
    """Bulk update attendance records"""
    try:
        data = request.get_json()
        attendance_ids = data.get('attendance_ids', [])
        action = data.get('action')
        new_status = data.get('status')
        
        if not attendance_ids:
            return jsonify({'error': 'No attendance records selected'}), 400
        
        if action == 'update_status' and new_status:
            # Update status for selected records
            updated_count = Attendance.query.filter(
                Attendance.id.in_(attendance_ids)
            ).update({'status': new_status}, synchronize_session=False)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Updated {updated_count} attendance records to {new_status}',
                'updated_count': updated_count
            })
        
        elif action == 'delete':
            # Delete selected records
            deleted_count = Attendance.query.filter(
                Attendance.id.in_(attendance_ids)
            ).delete(synchronize_session=False)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Deleted {deleted_count} attendance records',
                'deleted_count': deleted_count
            })
        
        else:
            return jsonify({'error': 'Invalid action or missing parameters'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin.route('/api/courses/by-semester/<int:semester>')
def get_courses_by_semester(semester):
    """Get courses filtered by semester"""
    courses = Course.query.filter_by(semester=semester, is_active=True).order_by(Course.course_name).all()
    
    return jsonify([{
        'id': course.id,
        'course_code': course.course_code,
        'course_name': course.course_name,
        'semester': course.semester
    } for course in courses])

@admin.route('/api/students/by-semester/<int:semester>')
def get_students_by_semester(semester):
    """Get students filtered by semester"""
    students = Student.query.filter_by(semester=semester).order_by(Student.last_name, Student.first_name).all()
    
    return jsonify([{
        'id': student.id,
        'student_id': student.student_id,
        'full_name': student.full_name,
        'semester': student.semester
    } for student in students])
