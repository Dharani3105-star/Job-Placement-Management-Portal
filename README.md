# Job & Placement Management Portal

A web-based Job & Placement Management Portal developed using Flask and SQLite.

The system allows students to register, browse job opportunities, apply for jobs with a PDF resume, and track their application status. Administrators can manage job postings, view applications, access resumes, and update application statuses.

## Features

### Student Features

- Student registration and login
- Secure password hashing
- Browse available jobs and internships
- Search jobs by title, company, or location
- View complete job details
- Apply for jobs
- PDF resume upload
- Duplicate application prevention
- View submitted applications
- Track application status
- Student dashboard
- Student profile
- Application date/time tracking

### Admin Features

- Admin login
- Admin dashboard
- Application statistics
- Search applications by student, email, job, or company
- Filter applications by status
- View uploaded resumes
- Update application status
- Add new jobs
- Edit existing jobs
- Delete jobs
- Manage job descriptions, skills, and eligibility
- View registered students

## Technologies Used

- Python
- Flask
- SQLite
- HTML5
- CSS3
- Jinja2
- Werkzeug

## Project Structure

```text
Job-Placement-Management-Portal/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── applications.html
│   ├── apply.html
│   ├── job_details.html
│   ├── admin_login.html
│   ├── admin.html
│   ├── add_job.html
│   └── edit_job.html
│
└── static/
    └── css/
        └── style.css