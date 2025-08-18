from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import qrcode
import base64
from io import BytesIO
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.course import CourseEnrollment
from app.models.database import db

student = Blueprint('student', __name__)

@student.before_request
@login_required
def require_student():
    if current_user.role != 'student':
        flash('Access denied: You must be a student to view this page.', 'danger')
        return redirect(url_for('auth.index'))

@student.route('/dashboard')
def dashboard():
    student_profile = Student.query.filter_by(user_id=current_user.id).first_or_404()

    recent_attendance = Attendance.query.filter_by(
        student_id=student_profile.id
    ).order_by(Attendance.check_in_time.desc()).limit(10).all()

    enrolled_courses = CourseEnrollment.query.filter_by(
        student_id=student_profile.id, is_active=True
    ).all()

    return render_template('student_dashboard.html',
                         student=student_profile,
                         recent_attendance=recent_attendance,
                         enrolled_courses=enrolled_courses)

@student.route('/attendance-history')
def attendance_history():
    student_profile = Student.query.filter_by(user_id=current_user.id).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    attendance_query = Attendance.query.filter_by(
        student_id=student_profile.id
    ).order_by(Attendance.check_in_time.desc())
    
    attendance_records = attendance_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('student_attendance_history.html',
                         student=student_profile,
                         attendance_records=attendance_records)

@student.route('/courses')
def courses():
    student_profile = Student.query.filter_by(user_id=current_user.id).first_or_404()
    
    enrolled_courses = CourseEnrollment.query.filter_by(
        student_id=student_profile.id, is_active=True
    ).all()
    
    return render_template('student_courses.html',
                         student=student_profile,
                         enrolled_courses=enrolled_courses)

@student.route('/id-card')
def id_card():
    student_profile = Student.query.filter_by(user_id=current_user.id).first_or_404()
    
    if not student_profile.nfc_tag_id:
        student_profile.generate_nfc_tag_id()
        db.session.commit()

    qr_data = f"NFC_CARD:{student_profile.nfc_tag_id}:{student_profile.student_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer)
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return render_template('id_card.html', student=student_profile, qr_code=img_str)

@student.route('/profile')
def profile():
    student_profile = Student.query.filter_by(user_id=current_user.id).first_or_404()
    
    return render_template('student_profile.html',
                         student=student_profile)