from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import qrcode
import base64
from io import BytesIO
from app.models.user import User
from app.models.student import Student
from app.models.course import Course, CourseEnrollment
from app.models.classroom import Classroom
from app.models.attendance import Attendance
from app.models.database import db

admin = Blueprint('admin', __name__)

@admin.before_request
@login_required
def require_admin():
    if current_user.role != 'admin':
        flash('Access denied: You must be an admin to view this page.', 'danger')
        return redirect(url_for('auth.index'))

@admin.route('/dashboard')
def admin_dashboard():
    total_students = Student.query.count()
    total_courses = Course.query.count()
    total_classrooms = Classroom.query.count()
    today_attendance = Attendance.query.filter(
        Attendance.check_in_time >= datetime.utcnow().date()
    ).count()

    stats = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_classrooms': total_classrooms,
        'today_attendance': today_attendance
    }
    return render_template('admin_dashboard.html', stats=stats)

@admin.route('/students')
def manage_students():
    students = Student.query.order_by(Student.last_name).all()
    courses = Course.query.order_by(Course.course_name).all()
    return render_template('manage_students.html', students=students, courses=courses)

@admin.route('/courses')
def manage_courses():
    courses = Course.query.order_by(Course.course_name).all()
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('manage_courses.html', courses=courses, teachers=teachers)

@admin.route('/attendance')
def attendance_records():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    attendance_query = Attendance.query.order_by(Attendance.check_in_time.desc())
    records = attendance_query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('attendance_records.html', records=records)

@admin.route('/temp-card/<int:student_id>')
def generate_temp_card(student_id):
    student = Student.query.get_or_404(student_id)
    if not student.temp_card_id:
        student.generate_temp_card_id()
        db.session.commit()

    qr_data = f"TEMP_CARD:{student.temp_card_id}:{student.student_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer)
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return render_template('temp_id_card.html', student=student, qr_code=img_str)
