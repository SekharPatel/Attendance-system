from datetime import datetime
from .database import db


class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer, default=3)
    department = db.Column(db.String(100))
    semester = db.Column(db.Integer, nullable=False, default=1)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('User', backref='teaching_courses')
    enrollments = db.relationship('CourseEnrollment', backref='course', lazy='dynamic')
    class_sessions = db.relationship('ClassSession', backref='course', lazy='dynamic')
    
    def __repr__(self):
        return f'<Course {self.course_code}: {self.course_name} (Semester {self.semester})>'

class CourseEnrollment(db.Model):
    __tablename__ = 'course_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id'),)


