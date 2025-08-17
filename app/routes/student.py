from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.course import CourseEnrollment

student = Blueprint('student', __name__)

@student.before_request
@login_required
def require_student():
    if current_user.role != 'student':
        flash('Access denied: You must be a student to view this page.', 'danger')
        return redirect(url_for('auth.index'))

@student.route('/dashboard')
def student_dashboard():
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