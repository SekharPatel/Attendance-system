from datetime import datetime
from .database import db
import uuid

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    department = db.Column(db.String(100))
    year = db.Column(db.Integer)
    nfc_tag_id = db.Column(db.String(100), unique=True)
    temp_card_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    attendances = db.relationship('Attendance', backref='student', lazy='dynamic')
    course_enrollments = db.relationship('CourseEnrollment', backref='student', lazy='dynamic')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def generate_temp_card_id(self):
        self.temp_card_id = str(uuid.uuid4())[:8].upper()
        return self.temp_card_id
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.full_name}>'