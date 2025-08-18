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
    semester = db.Column(db.Integer, nullable=False, default=1)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_semester_update = db.Column(db.DateTime)
    auto_progression_enabled = db.Column(db.Boolean, default=True)
    nfc_tag_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    attendances = db.relationship('Attendance', backref='student', lazy='dynamic')
    course_enrollments = db.relationship('CourseEnrollment', backref='student', lazy='dynamic')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def generate_nfc_tag_id(self):
        """Generates a unique NFC Tag ID."""
        if not self.nfc_tag_id:
            self.nfc_tag_id = str(uuid.uuid4())[:8].upper()
        return self.nfc_tag_id
    
    def should_progress_semester(self):
        """Check if student should be promoted to next semester based on enrollment time."""
        if not self.auto_progression_enabled or self.semester >= 8:
            return False
        
        # Calculate months since enrollment
        months_since_enrollment = (datetime.utcnow() - self.enrollment_date).days / 30.44  # Average days per month
        
        # Each semester is 6 months, calculate expected semester
        expected_semester = min(8, int(months_since_enrollment / 6) + 1)
        
        return expected_semester > self.semester
    
    def get_progression_info(self):
        """Get detailed information about semester progression eligibility."""
        if not self.auto_progression_enabled:
            return {
                'eligible': False,
                'reason': 'Auto-progression disabled',
                'current_semester': self.semester,
                'suggested_semester': self.semester
            }
        
        if self.semester >= 8:
            return {
                'eligible': False,
                'reason': 'Already in final semester',
                'current_semester': self.semester,
                'suggested_semester': self.semester
            }
        
        months_since_enrollment = (datetime.utcnow() - self.enrollment_date).days / 30.44
        expected_semester = min(8, int(months_since_enrollment / 6) + 1)
        
        return {
            'eligible': expected_semester > self.semester,
            'reason': f'Based on {months_since_enrollment:.1f} months since enrollment',
            'current_semester': self.semester,
            'suggested_semester': expected_semester,
            'months_enrolled': months_since_enrollment
        }
    
    def progress_to_semester(self, new_semester, force=False):
        """Progress student to a new semester with validation."""
        if not force and new_semester <= self.semester:
            return False, "New semester must be higher than current semester"
        
        if new_semester > 8:
            return False, "Cannot progress beyond semester 8"
        
        old_semester = self.semester
        self.semester = new_semester
        self.last_semester_update = datetime.utcnow()
        
        return True, f"Student progressed from semester {old_semester} to {new_semester}"
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.full_name} (Semester {self.semester})>'
