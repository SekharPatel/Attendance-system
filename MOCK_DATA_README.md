# Mock Data Generator

This script generates comprehensive mock data for the Student Attendance Management System.

## Prerequisites

1. **Initialize the database first:**
   ```bash
   python app.py init-db
   ```

2. **Create admin user:**
   ```bash
   python app.py create-admin
   ```

3. **Install Faker dependency (if not already installed):**
   ```bash
   pip install Faker==30.8.2
   ```
   Or install all requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the mock data generator:
```bash
python generate_mock_data.py
```

## Generated Data

The script creates realistic mock data for:

### Users & Authentication
- **15 Teachers** with usernames `teacher001` to `teacher015` (password: `teacher123`)
- **200 Students** with usernames `student0001` to `student0200` (password: `student123`)
- **1 Admin** user `admin` (password: `admin123`) - preserved if exists

### Academic Structure
- **40 Courses** across 8 semesters with realistic course codes and names
- **25 Classrooms** in different buildings with NFC reader IDs
- **Course Schedules** with 2-3 sessions per week, avoiding conflicts
- **Student Enrollments** with 4-6 courses per semester based on current semester

### Student Profiles
- Realistic names, emails, and phone numbers
- Student IDs in format `STU2024XXXX`
- Distributed across semesters (more students in lower semesters)
- Unique NFC tag IDs for each student
- Auto-progression enabled for 75% of students

### Attendance Data
- **12 weeks** of historical class sessions
- **Realistic attendance patterns** (85% average attendance rate)
- Multiple attendance methods: NFC (70%), Temp Card (20%), Manual (10%)
- Status distribution: Present (80%), Late (15%), Absent (5%)
- Check-in and check-out times with realistic variations

## Sample Login Credentials

After running the script, you can login with:

- **Admin:** `admin` / `admin123`
- **Teachers:** `teacher001` to `teacher015` / `teacher123`
- **Students:** `student0001` to `student0200` / `student123`

## Data Distribution

### Students by Semester
- Semester 1: ~50 students (25%)
- Semester 2: ~40 students (20%)
- Semester 3: ~30 students (15%)
- Semester 4: ~24 students (12%)
- Semester 5: ~20 students (10%)
- Semester 6: ~16 students (8%)
- Semester 7: ~12 students (6%)
- Semester 8: ~8 students (4%)

### Courses by Department
- Computer Science: 24 courses
- Information Technology: 6 courses
- Mathematics: 4 courses
- Physics: 2 courses
- English Literature: 2 courses
- Business Administration: 2 courses

## Performance Notes

- The script uses batch processing for attendance records to improve performance
- Total generation time: ~30-60 seconds depending on system performance
- Database size after generation: ~50MB with all mock data

## Troubleshooting

If you encounter errors:

1. **Database not initialized:** Run `python app.py init-db` first
2. **Import errors:** Ensure you're in the correct directory and virtual environment is activated
3. **Faker not found:** Install with `pip install Faker==30.8.2`
4. **Memory issues:** The script processes data in batches, but if you have memory constraints, you can reduce the number of students/weeks in the script

## Customization

You can modify the following parameters in `generate_mock_data.py`:

- `num_teachers=15` - Number of teacher accounts
- `num_students=200` - Number of student accounts  
- `num_classrooms=25` - Number of classrooms
- `weeks_back=12` - Weeks of historical attendance data
- Course data in `self.course_data` dictionary
- Department list in `self.departments`
- Attendance probability and patterns in `generate_attendance()`