from datetime import datetime
from .database import db


class Classroom(db.Model):
    __tablename__ = 'classrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    building = db.Column(db.String(50))
    capacity = db.Column(db.Integer)
    nfc_reader_id = db.Column(db.String(100), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    class_sessions = db.relationship('ClassSession', backref='classroom', lazy='dynamic')
    
    def __repr__(self):
        return f'<Classroom {self.room_number}>'

class ClassSession(db.Model):
    __tablename__ = 'class_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('Attendance', backref='class_session', lazy='dynamic')
    
    def __repr__(self):
        return f'<ClassSession {self.course.course_code} on {self.session_date}>'