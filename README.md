# Student Attendance Management

# System

A web-based application built with Flask to manage student attendance using QR codes and a potential for NFC integration. This system provides a simple and efficient way for administrators to manage students, courses, and track attendance, while students can view their records and access a temporary digital ID card.

---

## ✨ Features

### 󰞴 Admin Features

```
● Dashboard : At-a-glance view of key statistics like total students, courses, and today's attendance.
● Student Management : Add, view, and manage student profiles.
● Course Management : Create and manage courses.
● Temporary ID Card Generation : Generate a temporary ID card with a unique QR code for each student.
● Attendance Tracking : View detailed attendance records with filtering options.
```
### 󰳐 Student Features

```
● Dashboard : Personalized dashboard with profile information and enrolled courses.
● View Attendance : Check personal attendance history.
● Temporary ID Card : Access and view a personal temporary ID card with a QR code.
```
### 📡 API

```
● RESTful Endpoints : API for creating students, courses, and marking attendance.
● QR Code Attendance : Endpoint to mark attendance by submitting QR code data.
```
## 💻 Technology Stack

```
● Backend : Flask, SQLAlchemy, Flask-Login
● Frontend : HTML, CSS, JavaScript, Bootstrap 5
● Database : SQLite (default for development)
● QR Code Generation : qrcode library
● Environment Management : python-dotenv
```

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

   - **Python** (version 3.8 or higher)

   - **pip** (Python package installer)

   - **Git** (for cloning the repository)

---


## 🚀 Installation and Setup

Follow these steps to get the application running on your local machine. These instructions
are compatible with **Windows, macOS, and Linux**.

### 1. Clone the Repository

Open your terminal or command prompt and clone the project repository:
```   
git clone <your-repository-url>
cd student-attendance-system
```
### 2. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

**On macOS/Linux:**

```
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```
python -m venv .venv
.venv\Scripts\activate
```
### 3. Install Dependencies

Install all the required Python packages using the requirements.txt file:
```
pip install -r requirements.txt
```
### 4. Initialize the Database

This step creates the database file and all the necessary tables.
**Important** : If you have an old instance/attendance_system.db file, delete it first to start fresh.


- Run the following command from the root directory of the project (Attendance system):
```
python app.py init-db
```
- You will see the output: Initialized the database.

### 5. Create a Default Admin User

- Create the first administrative user to manage the system:

- Run the following command in your terminal
```
python app.py create-admin
```

- You will see the output: Default admin user created.
~
## ▶ Running the Application

- Once the setup is complete, you can start the Flask development server.
```
python app.py
```
- The application will be running and accessible at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---


## 📝 Usage

### Logging In

1. Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.
2. You will be redirected to the login page.
3. Use the default admin credentials to log in:
    ○ **Username** : admin
    ○ **Password** : admin

### Basic Workflow

1. **Log in as Admin** : Access the admin dashboard.
2. **Add a Student** : Navigate to Manage Students and add a new student profile.
3. **Generate ID Card** : Click the ID card icon next to a student's name to generate their
    temporary ID card with a QR code.
4. **Mark Attendance** : Use a QR code scanner app on your phone to scan the QR code. You
    can then use a tool like Postman or curl to send a POST request to the attendance API
    endpoint.

## 🌐 API Endpoints


Here are the primary API endpoints available:

### Mark Attendance

```
● URL : /api/attendance/mark
● Method : POST
● Description : Marks a student's attendance using the data from the QR code.
● Body (JSON) :

{"nfc_tag_id": "<id>","nfc_reader_id": "<id>"}

● Success Response (201) :
{
"message": "Attendance marked successfully",
"student_name": "Sekhar Patel",
"course": "Introduction to Programming",
"check_in_time": "2025-08-17T10:30:00.123456"
}
● Error Response (400/404) :
{
"error": "Invalid QR data format"
}
```
### Other Endpoints

```
● POST /api/students: Create a new student. (Admin only)
● GET /api/students: Get a list of all students. (Admin only)
● POST /api/courses: Create a new course. (Admin only)
● GET /api/courses: Get a list of all courses. (Admin only)
```
## 🔧 Troubleshooting

```
● sqlite3.OperationalError: no such table: students : This means the database was not
initialized. Run python app.py init-db to create the tables.
● Form is unresponsive ("Processing...") : This can be a JavaScript error. Check the
browser's developer console (F12) for errors. Ensure your HTML templates have all the
required elements that the JavaScript files interact with.
● TypeError when generating QR code : Ensure you have the correct version of the
qrcode and Pillow libraries installed. The requirements.txt file should manage this.
```
## 🔮 Future Enhancements

### Planned Features
- 🔄 Real NFC integration (requires hardware)
- 🔄 Advanced reporting and analytics
- 🔄 Email notifications
- 🔄 Bulk import/export functionality
- 🔄 Class scheduling system
- 🔄 Mobile application
- 🔄 Real-time dashboard updates
- 🔄 Attendance policies and rules

### Security Enhancements
- 🔄 Two-factor authentication
- 🔄 Password policies
- 🔄 Audit logging
- 🔄 Session management
- 🔄 Input validation and sanitization

### Performance Optimizations
- 🔄 Database indexing
- 🔄 Caching mechanisms
- 🔄 API rate limiting
- 🔄 Pagination improvements
- 🔄 Background task processing

## NFC Integration Notes

The system is designed to work with NFC tags embedded in ID cards. For testing:

1. **Temporary Cards**: Use the QR codes generated for temporary ID cards
2. **NFC Simulation**: The JavaScript includes NFC Web API code for future integration
3. **Hardware Requirements**: NFC readers and programmable NFC tags needed for full implementation

## Testing the System

1. **Admin Login**: Use admin/admin123 to access admin features
2. **Add Students**: Create student profiles with temporary ID cards
3. **Create Courses**: Add courses and assign teachers
4. **Generate Cards**: Print temporary ID cards for testing
5. **Manual Attendance**: Use API endpoints to test attendance marking

## Production Deployment

### Security Checklist
- [ ] Change default admin password
- [ ] Update SECRET_KEY in .env
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure HTTPS
- [ ] Set up proper logging
- [ ] Configure backup systems
- [ ] Implement monitoring

### Environment Setup
- [ ] Configure production database
- [ ] Set up Redis for caching
- [ ] Configure email service
- [ ] Set up reverse proxy (nginx)
- [ ] Configure SSL certificates
- [ ] Set up monitoring and alerts

## Support and Documentation

For additional help:
- Check the code comments for implementation details
- Review the API documentation in the routes files
- Test the system with provided sample data
- Extend functionality based on your specific requirements

## License
This system is developed for educational purposes and can be extended for production use with proper security measures.
'''

print("Student Attendance Management System has been created successfully!")
print("\nKey Components:")
print("- Flask backend with SQLAlchemy ORM")
print("- Responsive Bootstrap frontend")
print("- NFC and temporary ID card support")
print("- Complete admin and student interfaces")
print("- RESTful API for attendance management")
print("- QR code generation for testing")
print("\nRefer to the setup instructions in the code for deployment details.")
