# Employee Attendance Tracking System

This project is designed to track the daily check-in and check-out times of employees, monitor delays, and manage annual leave. Built using Django and PostgreSQL, this system offers separate access levels for personnel and authorized users.

## Project Overview

The application automatically records the first check-in and last check-out times for each employee daily. In case of tardiness, the system will notify the authorized personnel. Annual leave is deducted based on tardiness, and employees can view and request their leave, which can be approved or rejected by the authorized staff.
![image](https://github.com/user-attachments/assets/dea4aecf-7e61-4970-85d9-1f99eb7cdb5a)

### Key Features:

| **Feature**                    | **Description**                                                                                                      |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| **Work Start and End Times**    | Work hours are set from **08:00 AM** to **06:00 PM**.                                                                  |
| **Weekend Days**                | Saturdays and Sundays are considered holidays (non-working days).                                                     |
| **Automatic Leave Allocation**  | New employees are automatically assigned **15 days** of annual leave.                                                |
| **Tardiness Tracking**          | Employees' tardiness is tracked, and the time difference is deducted from their annual leave.                         |
| **Working Hours Report**        | Monthly working hours summary for each employee is provided.                                                         |
| **Leave Management**            | Employees can view their used leave days, and leave requests can be submitted for approval by staff.                  |
| **Notifications**               | Authorized personnel receive notifications for tardiness and when an employee's annual leave drops below 3 days.       |
| **Role-Based User System**      | Separate login/logout pages for **Personnel** and **Authorized Staff**.                                               |

### Bonus Features:
- **Celery Notification System**: Notifications are handled via Celery.
- **WebSocket Integration**: Real-time notifications via WebSocket.

## Technologies Used

| **Technology**              | **Purpose**                                                                                                           |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Backend**                 | Python, Django, Django Rest Framework, PostgreSQL                                                                     |
| **Frontend**                | HTML, CSS, JavaScript, Material UI                                                                                     |
| **Notifications**           | Celery, WebSocket                                                                                                     |
| **Database**                | PostgreSQL                                                                                                            |

## Setup and Installation

### 1. Clone the Repository

Clone the project repository to your local machine:

```bash
git clone https://github.com/your-username/2NTECH.git
cd 2NTECH
```

### 2. Install Dependencies
Install the required dependencies listed in requirements.txt:


```bash
pip install -r requirements.txt
```

### 3. Database Setup
Configure the PostgreSQL database and set up the connection in the settings.py file.

Create and apply the database migrations:
```bash
python manage.py migrate
```

### 4. Create Superuser
Create an admin user (superuser) to access the Django admin panel:
```bash
python manage.py createsuperuser
```

### 5. Start the Development Server
Start the development server:
```bash
python manage.py runserver
The application will now be available locally at http://127.0.0.1:8000/.
```



