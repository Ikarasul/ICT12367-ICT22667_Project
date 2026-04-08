# 🌴 DylanCompany — Modern Tour Management System
**ระบบจัดการบริษัททัวร์และจองตั๋วแบบครบวงจร**
*(Refactored with Modern Layouts & Print-Ready Architecture)*

---

## 📋 ภาพรวมระบบ (System Overview)
DylanCompany เป็นระบบบริหารจัดการทัวร์และการจองซึ่งถูกออกแบบประสบการณ์ผู้ใช้ (UX/UI) ใหม่ทั้งหมด โดยเน้นความทันสมัย ความชัดเจน และการใช้งานจริงของฝั่งแอดมินและพนักงาน ระบบถูกพัฒนาเต็มรูปแบบบน **Django** ควบคู่กับการใช้ **Tailwind CSS** ในการจัดการหน้าจอ (Template) 

ระบบครอบคลุมตั้งแต่หน้าล็อกอินแบบ Glassmorphism ไปจนถึงกระบวนการออก E-Ticket ที่พร้อมพิมพ์ลงกระดาษ A4 หน้าเดียว และ แดชบอร์ดสรุปข้อมูลการจองแบบ Real-time

---

## 🛠️ เทคโนโลยีและเครื่องมือที่ใช้ (Tech Stack & Tools)

| ส่วนของระบบ | เทคโนโลยีและการนำไปใช้งาน |
|-----------|-------------------------|
| **Back-end Server** | Python 3.11 + **Django 4.2** (รันคอร์ลอจิกและ Routing) |
| **Database** | Microsoft SQL Server (เชื่อมต่อผ่าน `managed=False` เข้ากับ Legacy DB) |
| **Front-end Design** | HTML5 + **Tailwind CSS** (ลบ React/Vite ออกเพื่อให้ Django Template เรนเดอร์ UI ตรงๆ เพื่อความรวดเร็วและเป็นอันหนึ่งอันเดียวกัน) |
| **Interactivity** | Vanilla JavaScript (ใช้ทำ Real-time Search กรองตารางแบบไม่ต้อง reload และระบบ Check-list) |
| **Icons & Fonts** | Google Fonts (Sarabun และ Plus Jakarta Sans) + Material Symbols |
| **UI Components** | SweetAlert2 (สำหรับการแจ้งเตือน Popup) |

---

## ✨ เค้าโครงสีหลักของแบรนด์ (Brand Theme)
- **Forest Green** (`#22c55e`, `#16a34a`): สีหลักแสดงออกถึงธรรมชาติ การกระทำหลัก (Action/Edit) และความสำเร็จ
- **Soft Pastel Pink** (`#f472b6`, `#be185d`): สีรองใช้สำหรับปุ่มลบ ยกเลิก หรือสร้างมิติคู่กับสีเขียว
- **Charcoal** (`#111827`): สีข้อความหลักที่เน้นความเป็น High-Contrast อ่านง่ายสบายตา

---

## 📖 คู่มือการใช้งานระบบ (User Manual)

### 1. แดชบอร์ดสำหรับแอดมิน (`/dashboard/`)
- **KPI Stats:** ตัวเลขรวมด้านบน 4 การ์ด (Total Bookings, Revenue, New Customers, Pending Payments) ดึงข้อมูลสดจากฐานข้อมูล
- **Interactive Tasks:** พนักงานสามารถทำงานรูทีน เช่น แจ้งเตือนสลิป, จำนวนคน, และกดขีดฆ่า Checklist ภายในตัวแดชบอร์ดได้ทันที ตัวระบบจะจัดการขีดฆ่า (Strikethrough) และเบลอข้อความให้อัตโนมัติด้วย JavaScript
- **Recent Bookings Search:** ใช้งานกล่องค้นหามุมขวาบนของตารางเพื่อค้นหา Booking ID หรือชื่อลูกค้าได้ทันที (พิมพ์ปุ๊บ กรองผลลัพธ์ปั๊บ เรียกว่า DOM Filtering โดยไม่ต้อง Refresh)

### 2. ระบบ E-Ticket และการปริ้นท์ (`/ticket/<id>/`)
- เข้าดู E-Ticket ได้ที่ระบบตรวจสอบการจอง ตัวตั๋วประกอบด้วยรายละเอียดลูกค้า QR Code และสถานะการจ่ายเงิน
- **วิธีสั่งพิมพ์ (Print):** กดปุ่ม Print จากแถบด้านบน (Toolbar) ระบบจะฉีด CSS พิเศษ (`@media print`) ที่ปรับกระดาษเข้าสู่หน้า A4 แนวตั้ง (Portrait) 
  - ระบบจะซ่อน Navigation, Sidebar แผงควบคุมทั้งหมด
  - ปรับสีตัวอักษรทุกตัวเป็นสีดำ `#000` เพื่อความคมชัดบนกระดาษ
  - ป้องกันการตัดหน้าครึ่งๆ กลางๆ ของตัวการ์ดตั๋ว (`page-break-inside: avoid`)

### 3. ตารางข้อมูลและการจัดการ (`/manage/`)
- แต่ละตารางฐานข้อมูล จะแสดงผลในรูปแบบการ์ดสะอาดตา 
- มีสไตล์สลับสีแถว (`even:bg-slate-50`) ช่วยให้อ่านข้อมูลแนวยาวง่ายขึ้น
- **ช่องค้นหาทันใจ (Search Bar):** ทำงานเหมือนในแดชบอร์ด แค่พิมพ์คำที่ต้องการ ตารางจะถูกกรองอัตโนมัติ
- **Action Buttons:** ปุ่ม Edit ถูกขยายขนาดด้วยสีเขียวเด่นชัด และปุ่ม Delete จะเป็นสีชมพูแดงเพื่อป้องกันการกดผิดพลาด (มี confirm dialog ก่อนลบเสมอ)

### 4. หน้าต่าง Audit Log (`/audit-log/`)
- ปรับเปลี่ยนจากตารางน่าเบื่อ ให้กลายเป็น **Vertical Timeline Feed (สายแนวตั้ง)**
- สี Node ของ Timeline จะเปลี่ยนขึ้นอยู่กับ Action (เขียว = INSERT, ฟ้า = UPDATE, แดง = DELETE)
- ชื่อผู้ทำรายการและ ID จะถูกเน้นด้วย Font-Black สีดำเข้ม `#111827` ทำให้สแกนตาอ่านการเปลี่ยนแปลงระบบได้อย่างรวดเร็ว

---

## 🔑 บัญชีสำหรับการทดสอบระบบ (Test Credentials)
สำหรับการเข้าสู่ระบบในฐานะพนักงานหรือผู้ดูแลระบบ สามารถใช้บัญชีจำลองดังต่อไปนี้:

| ระดับผู้เข้าใช้งาน (Role) | รหัสผู้ใช้ (Username) | รหัสผ่าน (Password) |
|-----------------------|-----------------------|-----------------------|
| 👑 **Administrator** (ผู้ดูแลระบบ) | `admin` | `admin123` |
| 🧑‍💻 **Staff** (พนักงานทั่วไป) | `staff` | `staff123` |

*(หมายเหตุ: กรณีที่รหัสนี้ไม่สามารถเข้าถึงได้ ให้รันคำสั่ง `python manage.py createsuperuser` ในเทอร์มินัลเพื่อสร้างบัญชีแอดมินของคุณเองใหม่)*

---

## ⚙️ ขั้นตอนการติดตั้งและตั้งค่าระบบ (Installation Guide)

เพื่อให้ระบบทำงานได้อย่างสมบูรณ์แบบ ทั้งในส่วนของ Backend (Django) และฐานข้อมูล (SQL Server) กรุณาทำตามขั้นตอนอย่างละเอียดดังนี้:

### 🧰 สิ่งที่ต้องติดตั้งไว้ในเครื่องก่อน (Prerequisites)
1. **Python 3.11** หรือใหม่กว่า
2. **Microsoft SQL Server** (เวอร์ชั่น Express ก็ใช้งานได้) พร้อมด้วยโปรแกรม **SSMS** (SQL Server Management Studio)
3. **ODBC Driver 17 for SQL Server** (จำเป็นสำหรับให้ Python เชื่อมต่อ Database ได้)
4. **Git** เดสก์ท็อป

---

### Step 1: ดาวน์โหลดโปรเจกต์
ดึงซอร์สโค้ดล่าสุดจากฐานเก็บข้อมูลลงมายังเครื่องของคุณ
```bash
git clone https://github.com/Ikarasul/ICT12367-ICT22667_Project.git
cd ICT12367-ICT22667_Project
cd tourproject
```

### Step 2: สร้างอ้อมกอดเสมือน (Virtual Environment)
เพื่อไม่ให้ไลบรารีของโปรเจกต์นี้ไปตีกับโปรเจกต์อื่น กรุณาสร้าง venv และติดตั้ง dependencies:
```bash
# สร้าง Environment ชื่อ venv
python -m venv venv

# Activate Environment (สำหรับ Windows)
venv\Scripts\activate
# หากใช้ Mac/Linux ให้ใช้: source venv/bin/activate

# ติดตั้งแพคเกจทั้งหมดที่จำเป็น
pip install -r requirements.txt
```

### Step 3: เตรียมฐานข้อมูล (Database Setup)
เนื่องจากระบบใช้โครงสร้างตาราง (Schema) ขนาดใหญ่ เราจึงต้องใช้สคริปต์ SQL ในการสร้างรวดเดียว
1. เปิดโปรแกรม **SQL Server Management Studio (SSMS)**
2. ล็อคอินเข้าสู่ Server ของคุณ (จำ `Server Name` ไว้ให้ดี)
3. ไปที่เมนู File > Open > File... แล้วเลือกไฟล์ `database/TourCompanyDB.sql` ที่อยู่ในโฟลเดอร์โปรเจกต์
4. กดปุ่ม **Execute** (หรือ F5) เพื่อสร้างตารางข้อมูลทั้งหมด

### Step 4: เชื่อมต่อ Django เข้ากับ SQL Server
ตั้งค่าข้อมูลความลับของระบบ เช่น พาสเวิร์ดเชื่อมต่อฐานข้อมูล
1. คัดลอกไฟล์ `.env.example` แล้วเปลี่ยนชื่อเป็น `.env`
2. เปิดไฟล์ `.env` ขึ้นมาแก้ไขค่าต่อไปนี้ให้ตรงกับ SQL Server ของคุณ:
```env
DB_NAME=TourCompanyDB
DB_USER=sa        # หรือ username อื่นๆ ที่มีสิทธิ์ถึง database
DB_PASSWORD=your_sql_password_here
DB_HOST=localhost # หรือชื่อ Server Name ของคุณ (เช่น DESKTOP-AAAA\SQLEXPRESS)
DB_PORT=1433
```

### Step 5: ทดสอบเปิดเซิร์ฟเวอร์ (Run Local Server)
โดยปกติข้อมูลในฐานข้อมูลของเรามาจากไฟล์ SQL แล้ว จึงไม่จำเป็นต้อง `migrate` โครงสร้างเพิ่มให้ซ้ำซ้อน
```bash
python manage.py runserver
```

> **🎉 ยินดีด้วย! ระบบพร้อมใช้งานแล้ว**
> เปิดบราวเซอร์ของคุณแล้วไปที่:
> - **หน้าหลัก / แดชบอร์ด:** http://localhost:8000/dashboard/
> - **ระบบเจ้าหน้าที่ (Login):** http://localhost:8000/login/

---

*ระบบได้รับการรีแฟกเตอร์ UI อย่างพิถีพิถัน พร้อมสำหรับการทำงานของธุรกิจแบบ Production-Ready*
