from .database import db
from datetime import datetime


class Attendance(db.Model):
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_session_id = db.Column(db.Integer, db.ForeignKey('class_sessions.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='present')  # present, absent, late
    method = db.Column(db.String(20), default='nfc')  # nfc, manual, temp_card
    notes = db.Column(db.Text)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'class_session_id'),)
    
    def __repr__(self):
        return f'<Attendance {self.student.full_name} - {self.class_session.course.course_code}>'