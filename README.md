🚍 MoveSphere – Cloud-Based Bus Pass & Ticket Booking System
📌 Project Overview

MoveSphere is a cloud-hosted Bus Pass and Ticket Management System that enables users to register, purchase bus passes, book tickets, generate QR-based travel credentials, make payments, and download travel documents digitally.

The system eliminates traditional paper-based passes and tickets by leveraging cloud technologies such as AWS S3, AWS RDS, FastAPI, and Netlify.

This project was developed as a Cloud Computing Mini Project with a focus on:

Digital transportation management
QR-based verification
Cloud storage
Scalable web deployment
Secure user authentication
Real-time database management

The backend APIs and core functionalities are implemented using FastAPI and MySQL while AWS cloud services provide storage and database capabilities. The implementation includes user registration, login, bus pass generation, ticket booking, payment processing, PDF generation, QR code generation, and cloud deployment.

🎯 Objectives
Eliminate paper-based bus passes and tickets
Prevent ticket loss and misuse
Enable online booking and verification
Provide secure cloud-based storage
Generate QR-based travel credentials
Improve passenger convenience
Maintain centralized transportation records
Enable easy scalability using cloud infrastructure
🏗️ System Architecture
+----------------------+
|     Frontend UI      |
|  HTML / CSS / JS     |
|   (Netlify Hosted)   |
+----------+-----------+
           |
           |
           v
+----------------------+
|     FastAPI API      |
|   (Render Hosting)   |
+----------+-----------+
           |
           |
  +--------+---------+
  |                  |
  v                  v
+--------+     +-----------+
| AWS S3 |     | AWS RDS   |
| Storage|     | MySQL DB  |
+--------+     +-----------+
☁️ Cloud Services Used
Service	Purpose
AWS RDS MySQL	Database Storage
AWS S3	QR Code & PDF Storage
Render	Backend Deployment
Netlify	Frontend Deployment
GitHub	Version Control
FastAPI	REST API Backend
🛠️ Tech Stack
Backend
Python 3.11
FastAPI
SQLAlchemy
Pydantic
Uvicorn
Database
MySQL
AWS RDS
Storage
AWS S3
Security
Passlib (bcrypt)
Password Hashing
PDF & QR Generation
ReportLab
QRCode
Deployment
Render
Netlify
📂 Project Structure
MoveSphere/
│
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── s3_utils.py
│   ├── requirements.txt
│   ├── runtime.txt
│   └── .env
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│
├── qr_codes/
│   ├── passes/
│   └── tickets/
│
├── pdfs/
│   ├── passes/
│   └── tickets/
│
└── README.md
✨ Features
User Management
User Registration
User Login
Password Hashing
User Profile Retrieval
Bus Pass Module
Apply for Bus Pass
Generate QR Code
Generate PDF Pass
Store QR and PDF in AWS S3
Verify Pass
Ticket Booking Module
Book Bus Ticket
Dynamic Fare Calculation
QR Ticket Generation
PDF Ticket Generation
Upload Ticket Assets to AWS S3
Payment Module
Payment Processing
Revenue Tracking
Payment History
Admin Module
View Payments
View Statistics
Monitor Users
Monitor Tickets
Monitor Passes
Verification Module
Verify Bus Pass
Verify Ticket
🗄️ Database Design
Users Table
users
Column
user_id
name
email
password
phone
Bus Passes Table
bus_passes
Column
pass_id
user_id
pass_type
issue_date
expiry_date
qr_code
qr_url
pdf_url
Tickets Table
tickets
Column
ticket_id
user_id
source
destination
fare
booking_date
qr_code
qr_url
pdf_url
Payments Table
payments
Column
payment_id
user_id
amount
payment_status
payment_date
🔌 API Endpoints
Authentication
POST /register
POST /login
Bus Pass
POST /apply-pass
GET  /passes
GET  /verify-pass/{id}
GET  /download-pass/{id}
Tickets
POST /book-ticket
GET  /tickets
GET  /verify-ticket/{id}
GET  /download-ticket/{id}
Payments
POST /make-payment
GET  /payments
GET  /admin/payments
User
GET /user/{id}
GET /user/{id}/passes
GET /user/{id}/tickets
Admin
GET /admin/stats
Health
GET /health

The backend exposes endpoints for registration, login, pass application, ticket booking, payment handling, verification, and administrative statistics. QR codes and PDFs are generated and uploaded to AWS S3 as part of the workflow.

🔐 Security Features
Password hashing using bcrypt
Secure API communication
Cloud database isolation using AWS RDS
AWS IAM credentials for S3 access
CORS protection
⚙️ Environment Variables

Create a .env file:

DATABASE_URL=mysql+pymysql://username:password@host/bus_pass_system

AWS_ACCESS_KEY_ID=YOUR_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET
AWS_REGION=ap-south-1
AWS_BUCKET_NAME=YOUR_BUCKET_NAME
🚀 Deployment
Backend (Render)
Build Command
pip install -r requirements.txt
Start Command
uvicorn main:app --host 0.0.0.0 --port $PORT
Frontend (Netlify)
Upload frontend folder
Update API base URL
const API_BASE =
"https://movesphere.onrender.com";
Deploy
📊 Future Enhancements
JWT Authentication
Online Payment Gateway Integration
Mobile Application
GPS-Based Bus Tracking
Notification System
Admin Dashboard Analytics
Multi-City Route Management
Digital Wallet Support
Email/SMS Alerts
QR Scanner Validation App
🎓 Learning Outcomes

Through this project, the following concepts were implemented:

Cloud Computing
REST API Development
FastAPI Framework
AWS RDS
AWS S3
SQLAlchemy ORM
QR Code Generation
PDF Generation
Cloud Deployment
Authentication & Security
Database Management
Frontend–Backend Integration
👨‍💻 Author

Ruchir Vyas
B.E. Computer Science & Engineering
(IoT, Cyber Security & Blockchain Technology)
MVSR Engineering College, Hyderabad

Project

MoveSphere – Cloud-Based Bus Pass & Ticket Booking System
