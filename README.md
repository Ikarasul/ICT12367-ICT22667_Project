# 🌏 ระบบจัดการบริษัททัวร์
### ICT12367 / ICT22667 — โปรเจกต์วิชาการพัฒนาระบบสารสนเทศ

---

## 📋 ภาพรวมระบบ

ระบบจัดการบริษัททัวร์ครบวงจร พัฒนาด้วย Django REST Framework และ React  
รองรับการจัดการลูกค้า แพ็กเกจทัวร์ กำหนดการเดินทาง ไกด์นำเที่ยว และการจองตั๋ว/โรงแรม

---

## 🛠️ Tech Stack

| ส่วน | เทคโนโลยี |
|------|-----------|
| Back-end | Python 3.11 + Django 4.2 + Django REST Framework |
| Database | Microsoft SQL Server (SSMS) |
| Front-end | React + Vite + Tailwind CSS |
| Authentication | JWT (djangorestframework-simplejwt) |
| Deploy (API) | Railway |
| Deploy (Web) | Vercel |

---

## 📁 โครงสร้างโปรเจกต์

```
tourproject/
├── apps/
│   ├── accounts/        # พนักงาน + ระบบ Login
│   ├── customers/       # ลูกค้า + กลุ่มลูกค้า + รีวิว
│   ├── tours/           # แพ็กเกจทัวร์ + รอบทัวร์ + โปรแกรมรายวัน
│   ├── bookings/        # การจอง + ผู้โดยสาร + ตั๋วเครื่องบิน
│   ├── payments/        # การชำระเงิน + ค่าใช้จ่าย
│   ├── resources/       # ไกด์ + ยานพาหนะ + โรงแรม
│   ├── reports/         # รายงานและสถิติ
│   └── notifications/   # การแจ้งเตือน
├── database/
│   └── TourCompanyDB.sql   # SQL Script สร้างตารางทั้งหมด
├── tourproject/
│   ├── settings.py
│   └── urls.py
├── .env.example         # ตัวอย่างการตั้งค่า
├── manage.py
└── requirements.txt
```

---

## 🗄️ ฐานข้อมูล — 18 ตาราง

| กลุ่ม | ตาราง |
|-------|-------|
| ผู้ใช้งาน | Employees, CustomerGroups, Customers, CustomerReviews |
| แพ็กเกจ | TourPackages, PackageItinerary, PackageImages, PromoCodes |
| กำหนดการ | TourSchedules, TourHotels, TourItineraryLogs, TourDocuments |
| การจอง | Bookings, BookingPassengers, FlightTickets |
| การเงิน | Payments, Expenses |
| ทรัพยากร | Guides, GuideAvailability, Vehicles, Hotels |
| แจ้งเตือน | Notifications |

---

## ⚙️ วิธีติดตั้งและรัน

### สิ่งที่ต้องมีก่อน
- Python 3.11+
- SQL Server + SSMS
- ODBC Driver 17 for SQL Server
- Node.js 18+

### 1. Clone โปรเจกต์
```bash
git clone https://github.com/Ikarasul/ICT12367-ICT22667_Project.git
cd ICT12367-ICT22667_Project
```

### 2. ตั้งค่า Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. ตั้งค่าฐานข้อมูล
- เปิด SSMS รัน `database/TourCompanyDB.sql`
- copy ไฟล์ `.env.example` → `.env`
- แก้ไข password SQL Server ในไฟล์ `.env`

### 4. Migrate และรันเซิร์ฟเวอร์
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 5. เปิดระบบ
- **Django Admin:** http://localhost:8000/admin
- **API:** http://localhost:8000/api/

---

## 🌐 API Endpoints หลัก

| Method | Endpoint | ฟังก์ชัน |
|--------|----------|---------|
| POST | `/api/auth/login/` | เข้าสู่ระบบ |
| GET/POST | `/api/customers/` | จัดการลูกค้า |
| GET/POST | `/api/tours/packages/` | จัดการแพ็กเกจ |
| GET/POST | `/api/tours/schedules/` | จัดการรอบทัวร์ |
| GET/POST | `/api/bookings/` | จัดการการจอง |
| GET/POST | `/api/payments/` | จัดการชำระเงิน |
| GET | `/api/reports/dashboard/` | ข้อมูล Dashboard |

---

## 👥 ทีมพัฒนา

| ชื่อ | รหัสนักศึกษา | หน้าที่ |
|------|-------------|---------|
| [ชื่อสมาชิก 1] | ICT12367 | Full-stack Developer |
| [ชื่อสมาชิก 2] | ICT22667 | UI/UX + Testing |
| [ชื่อสมาชิก 3] | - | Database + Documentation |

---

## 📌 สถานะโปรเจกต์

- [x] ออกแบบฐานข้อมูล (18 ตาราง)
- [x] Django Models + Migration
- [ ] Django REST API
- [ ] React Admin Dashboard
- [ ] หน้าเว็บลูกค้า
- [ ] Deploy ขึ้น Cloud

---

*พัฒนาเพื่อการศึกษา — สาขาวิชาเทคโนโลยีสารสนเทศและการสื่อสาร*
