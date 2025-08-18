from datetime import datetime, time, date
from .database import db
import json


class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    exclusion_dates = db.Column(db.Text)  # JSON string of excluded dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='schedules')
    classroom = db.relationship('Classroom', backref='schedules')
    
    @property
    def exclusion_dates_list(self):
        """Get exclusion dates as a list of date objects."""
        if not self.exclusion_dates:
            return []
        try:
            date_strings = json.loads(self.exclusion_dates)
            return [datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in date_strings]
        except (json.JSONDecodeError, ValueError):
            return []
    
    @exclusion_dates_list.setter
    def exclusion_dates_list(self, dates):
        """Set exclusion dates from a list of date objects or strings."""
        if not dates:
            self.exclusion_dates = None
            return
        
        date_strings = []
        for date_obj in dates:
            if isinstance(date_obj, str):
                # Validate date string format
                try:
                    datetime.strptime(date_obj, '%Y-%m-%d')
                    date_strings.append(date_obj)
                except ValueError:
                    continue
            elif isinstance(date_obj, date):
                date_strings.append(date_obj.strftime('%Y-%m-%d'))
        
        self.exclusion_dates = json.dumps(date_strings) if date_strings else None
    
    def is_excluded_date(self, check_date):
        """Check if a specific date is excluded from the schedule."""
        if isinstance(check_date, str):
            check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        
        return check_date in self.exclusion_dates_list
    
    def get_day_name(self):
        """Get the day name for the day_of_week."""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else 'Unknown'
    
    def get_time_range(self):
        """Get formatted time range string."""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    def has_conflict_with(self, other_schedule):
        """Check if this schedule conflicts with another schedule."""
        if not isinstance(other_schedule, Schedule):
            return False
        
        # Different days don't conflict
        if self.day_of_week != other_schedule.day_of_week:
            return False
        
        # Different classrooms don't conflict
        if self.classroom_id != other_schedule.classroom_id:
            return False
        
        # Check time overlap
        return (self.start_time < other_schedule.end_time and 
                self.end_time > other_schedule.start_time)
    
    @classmethod
    def find_conflicts(cls, course_id, classroom_id, day_of_week, start_time, end_time, exclude_id=None):
        """Find conflicting schedules for the given parameters."""
        query = cls.query.filter(
            cls.classroom_id == classroom_id,
            cls.day_of_week == day_of_week,
            cls.is_active == True,
            cls.start_time < end_time,
            cls.end_time > start_time
        )
        
        if exclude_id:
            query = query.filter(cls.id != exclude_id)
        
        return query.all()
    
    def validate_schedule(self):
        """Validate the schedule for conflicts and logical consistency."""
        errors = []
        
        # Check if start time is before end time
        if self.start_time >= self.end_time:
            errors.append("Start time must be before end time")
        
        # Check day of week range
        if not (0 <= self.day_of_week <= 6):
            errors.append("Day of week must be between 0 (Monday) and 6 (Sunday)")
        
        # Check semester range
        if not (1 <= self.semester <= 8):
            errors.append("Semester must be between 1 and 8")
        
        # Check for conflicts with other schedules
        conflicts = self.find_conflicts(
            self.course_id, 
            self.classroom_id, 
            self.day_of_week, 
            self.start_time, 
            self.end_time,
            exclude_id=self.id
        )
        
        if conflicts:
            conflict_courses = [conflict.course.course_code for conflict in conflicts]
            errors.append(f"Schedule conflicts with: {', '.join(conflict_courses)}")
        
        return errors
    
    def __repr__(self):
        return f'<Schedule {self.course.course_code} - {self.get_day_name()} {self.get_time_range()}>'