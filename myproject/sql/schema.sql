-- ==========================================================
-- schema.sql  ·  TourSongkhla  ·  Clean 10-Table Schema
-- Land-based Tour in Songkhla (No FlightTickets, No TourHotels)
-- รันใน SSMS หรือผ่าน setup_db.py
-- ==========================================================

USE TourSongkhla;
GO

-- ----------------------------------------------------------
-- 1. DROP ALL FOREIGN KEY CONSTRAINTS (dynamic — ล้าง FK ทั้งหมดก่อน)
-- ----------------------------------------------------------
DECLARE @drop_fk NVARCHAR(MAX) = N'';
SELECT @drop_fk += N'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id))
    + '.' + QUOTENAME(OBJECT_NAME(parent_object_id))
    + ' DROP CONSTRAINT ' + QUOTENAME(name) + ';' + CHAR(13)
FROM sys.foreign_keys;
IF LEN(@drop_fk) > 0
    EXEC sp_executesql @drop_fk;
GO

-- ----------------------------------------------------------
-- 2. DROP VIEWS
-- ----------------------------------------------------------
IF OBJECT_ID('vw_ScheduleAvailability', 'V') IS NOT NULL DROP VIEW vw_ScheduleAvailability;
IF OBJECT_ID('vw_FlightTickets',        'V') IS NOT NULL DROP VIEW vw_FlightTickets;
IF OBJECT_ID('vw_BookingSummary',       'V') IS NOT NULL DROP VIEW vw_BookingSummary;
IF OBJECT_ID('vw_AuditLog',             'V') IS NOT NULL DROP VIEW vw_AuditLog;
IF OBJECT_ID('vw_PackageRevenue',       'V') IS NOT NULL DROP VIEW vw_PackageRevenue;
GO

-- ----------------------------------------------------------
-- 3. DROP STORED PROCEDURES
-- ----------------------------------------------------------
IF OBJECT_ID('sp_Login',             'P') IS NOT NULL DROP PROCEDURE sp_Login;
IF OBJECT_ID('sp_LoginCustomer',     'P') IS NOT NULL DROP PROCEDURE sp_LoginCustomer;
IF OBJECT_ID('sp_RegisterCustomer',  'P') IS NOT NULL DROP PROCEDURE sp_RegisterCustomer;
IF OBJECT_ID('sp_CreateBooking',     'P') IS NOT NULL DROP PROCEDURE sp_CreateBooking;
IF OBJECT_ID('sp_WriteAuditLog',     'P') IS NOT NULL DROP PROCEDURE sp_WriteAuditLog;
GO

-- ----------------------------------------------------------
-- 4. DROP ALL TABLES (dynamic — ลบตารางทั้งหมดที่มีใน DB)
-- ----------------------------------------------------------
DECLARE @drop_tables NVARCHAR(MAX) = N'';
SELECT @drop_tables += N'DROP TABLE ' + QUOTENAME(TABLE_SCHEMA)
    + '.' + QUOTENAME(TABLE_NAME) + ';' + CHAR(13)
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND TABLE_NAME != 'sysdiagrams';   -- เก็บ sysdiagrams ไว้ (system table)
IF LEN(@drop_tables) > 0
    EXEC sp_executesql @drop_tables;
GO

-- ----------------------------------------------------------
-- 4. CREATE TABLES  (10 tables — No FlightTickets, No TourHotels)
-- ----------------------------------------------------------

-- 1. Customers
CREATE TABLE Customers (
    CustomerID   INT           IDENTITY(1,1) PRIMARY KEY,
    FullName     NVARCHAR(100) NOT NULL,
    Email        NVARCHAR(255) NOT NULL UNIQUE,
    Phone        NVARCHAR(20)  NULL,
    Passport     NVARCHAR(50)  NULL,
    DateOfBirth  DATE          NULL,
    Nationality  NVARCHAR(50)  NULL,
    Address      NVARCHAR(MAX) NULL,
    PasswordHash NVARCHAR(255) NOT NULL,
    CreatedDate  DATETIME      NOT NULL DEFAULT GETDATE()
);
GO

-- 2. Employees
CREATE TABLE Employees (
    EmployeeID   INT           IDENTITY(1,1) PRIMARY KEY,
    FullName     NVARCHAR(100) NOT NULL,
    Email        NVARCHAR(255) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(255) NOT NULL,
    Role         NVARCHAR(50)  NOT NULL DEFAULT 'Sales',  -- Admin | Sales | Accounting
    IsActive     BIT           NOT NULL DEFAULT 1,
    CreatedDate  DATETIME      NOT NULL DEFAULT GETDATE()
);
GO

-- 3. Guides
CREATE TABLE Guides (
    GuideID    INT           IDENTITY(1,1) PRIMARY KEY,
    FullName   NVARCHAR(100) NOT NULL,
    Phone      NVARCHAR(20)  NULL,
    Email      NVARCHAR(255) NULL,
    Languages  NVARCHAR(255) NULL,
    IsActive   BIT           NOT NULL DEFAULT 1
);
GO

-- 4. Hotels
CREATE TABLE Hotels (
    HotelID       INT           IDENTITY(1,1) PRIMARY KEY,
    HotelName     NVARCHAR(200) NOT NULL,
    Location      NVARCHAR(255) NULL,
    StarRating    TINYINT       NULL CHECK (StarRating BETWEEN 1 AND 5),
    PricePerNight DECIMAL(10,2) NULL
);
GO

-- 5. Vehicles
CREATE TABLE Vehicles (
    VehicleID   INT           IDENTITY(1,1) PRIMARY KEY,
    VehicleType NVARCHAR(100) NOT NULL,
    Capacity    INT           NULL,
    PlateNumber NVARCHAR(20)  NULL
);
GO

-- 6. TourPackages
CREATE TABLE TourPackages (
    PackageID      INT            IDENTITY(1,1) PRIMARY KEY,
    PackageName    NVARCHAR(255)  NOT NULL,
    TourName_en    NVARCHAR(255)  NULL,
    Destination    NVARCHAR(255)  NOT NULL,
    Destination_en NVARCHAR(255)  NULL,
    PricePerPerson DECIMAL(10,2)  NOT NULL DEFAULT 0,
    Description    NVARCHAR(MAX)  NULL,
    ImageURL       NVARCHAR(500)  NULL,
    DurationDays   INT            NULL,
    CreatedDate    DATETIME       NOT NULL DEFAULT GETDATE()
);
GO

-- 7. TourSchedules
CREATE TABLE TourSchedules (
    ScheduleID    INT      IDENTITY(1,1) PRIMARY KEY,
    PackageID     INT      NOT NULL REFERENCES TourPackages(PackageID),
    DepartureDate DATE     NOT NULL,
    ReturnDate    DATE     NOT NULL,
    TotalSeats    INT      NOT NULL DEFAULT 20,
    GuideID       INT      NULL REFERENCES Guides(GuideID)
);
GO

-- 8. Bookings
CREATE TABLE Bookings (
    BookingID    INT          IDENTITY(1,1) PRIMARY KEY,
    CustomerID   INT          NOT NULL REFERENCES Customers(CustomerID),
    ScheduleID   INT          NOT NULL REFERENCES TourSchedules(ScheduleID),
    NumAdults    INT          NOT NULL DEFAULT 1,
    NumChildren  INT          NOT NULL DEFAULT 0,
    BookingDate  DATETIME     NOT NULL DEFAULT GETDATE(),
    Status       NVARCHAR(20) NOT NULL DEFAULT 'Pending'
        CHECK (Status IN ('Pending','Confirmed','Cancelled'))
);
GO

-- 9. Payments
CREATE TABLE Payments (
    PaymentID     INT           IDENTITY(1,1) PRIMARY KEY,
    BookingID     INT           NOT NULL REFERENCES Bookings(BookingID),
    Amount        DECIMAL(12,2) NOT NULL,
    PaymentDate   DATETIME      NOT NULL DEFAULT GETDATE(),
    PaymentMethod NVARCHAR(50)  NULL,
    Status        NVARCHAR(20)  NOT NULL DEFAULT 'Pending'
        CHECK (Status IN ('Pending','Completed','Failed','Refunded'))
);
GO

-- 10. AuditLogs
CREATE TABLE AuditLogs (
    LogID       INT           IDENTITY(1,1) PRIMARY KEY,
    TableName   NVARCHAR(100) NOT NULL,
    Action      NVARCHAR(50)  NOT NULL,
    PerformedBy INT           NULL,
    Details     NVARCHAR(MAX) NULL,
    LogDate     DATETIME      NOT NULL DEFAULT GETDATE()
);
GO

-- ----------------------------------------------------------
-- 5. SAMPLE DATA
-- ----------------------------------------------------------

-- Guides (มัคคุเทศก์ประจำสงขลา)
INSERT INTO Guides (FullName, Phone, Languages, IsActive) VALUES
(N'สมชาย ท่องเที่ยว',  '081-111-1001', N'Thai, English',       1),
(N'Nattapong Sirichai', '081-111-1002', N'Thai, English, Chinese', 1),
(N'Lalita Malee',       '081-111-1003', N'Thai, English',       1);
GO

-- Hotels (โรงแรมในสงขลาและใกล้เคียง)
INSERT INTO Hotels (HotelName, Location, StarRating, PricePerNight) VALUES
(N'BP Samila Beach Hotel',       N'Songkhla, Thailand',    4, 2500),
(N'Haad Kaew Resort',            N'Songkhla, Thailand',    3, 1800),
(N'The Baipho Boutique Hotel',   N'Hat Yai, Thailand',     4, 2200),
(N'Lee Gardens Plaza Hotel',     N'Hat Yai, Thailand',     4, 1900),
(N'Centara Hat Yai',             N'Hat Yai, Thailand',     4, 2800);
GO

-- Vehicles
INSERT INTO Vehicles (VehicleType, Capacity, PlateNumber) VALUES
(N'Van (12 seats)',    12, N'สข-1234'),
(N'Minibus (20 seats)',20, N'สข-5678'),
(N'Coach (40 seats)', 40, N'สข-9012');
GO

-- TourPackages (ทัวร์ในจังหวัดสงขลาและภาคใต้)
INSERT INTO TourPackages (PackageName, TourName_en, Destination, Destination_en, PricePerPerson, DurationDays, Description) VALUES
(N'สงขลา เมืองเก่า 1 วัน',         N'Songkhla Old Town 1D',      N'สงขลา',             N'Songkhla',          1200,  1, N'เที่ยวเมืองเก่าสงขลา บ้านขนมเปี๊ยะ คาบสมุทรสทิงพระ'),
(N'หาดใหญ่ ช้อปปิ้ง 1 วัน',        N'Hat Yai Shopping 1D',       N'หาดใหญ่ สงขลา',    N'Hat Yai, Songkhla', 900,   1, N'ช้อปปิ้งตลาดกิมหยง ตลาดสันติสุข ไหว้พระ'),
(N'เกาะหนู เกาะแมว 2 วัน',         N'Ko Nu Ko Maeo 2D',          N'สงขลา',             N'Songkhla',          2800,  2, N'ล่องเรือชมเกาะ ดำน้ำดูปะการัง ชมพระอาทิตย์ตก'),
(N'ทะเลสาบสงขลา 1 วัน',            N'Songkhla Lake Tour 1D',     N'ทะเลสาบสงขลา',      N'Songkhla Lake',     1500,  1, N'ล่องเรือทะเลสาบ หมู่บ้านชาวประมง ชิมอาหารทะเล'),
(N'สตูล เกาะตะรุเตา 3 วัน',        N'Satun Tarutao 3D',          N'สตูล',              N'Satun',             5900,  3, N'อุทยานแห่งชาติตะรุเตา เกาะหลีเป๊ะ ดำน้ำ'),
(N'ปัตตานี ประวัติศาสตร์ 1 วัน',    N'Pattani Heritage 1D',       N'ปัตตานี',           N'Pattani',           1300,  1, N'มัสยิดกรือเซะ ลิมโกะเหนี่ย ชายหาดปัตตานี'),
(N'นครศรีธรรมราช 2 วัน',           N'Nakhon Si Thammarat 2D',    N'นครศรีธรรมราช',    N'Nakhon Si Thammarat',3200, 2, N'วัดพระมหาธาตุ อุทยานแห่งชาติเขาหลวง'),
(N'สงขลา-พัทลุง ธรรมชาติ 2 วัน',   N'Songkhla-Phatthalung 2D',   N'สงขลา-พัทลุง',     N'Songkhla-Phatthalung',2500,2, N'เขาพับผ้า ทะเลน้อย นกน้ำ'),
(N'หาดสมิหลา ซีฟู้ด 1 วัน',        N'Samila Beach Seafood 1D',   N'หาดสมิหลา สงขลา',  N'Samila Beach',      1100,  1, N'หาดสมิหลา นางเงือก ตลาดอาหารทะเล'),
(N'ทัวร์ 3 จังหวัด ชายแดน 3 วัน',   N'3 Southern Provinces 3D',   N'สงขลา-ยะลา-นราธิวาส',N'South Border 3D', 4500,  3, N'วัฒนธรรมชายแดนใต้ ตลาดชายแดน อาหารพื้นเมือง');
GO

-- TourSchedules (2 ตารางต่อแพ็กเกจ)
INSERT INTO TourSchedules (PackageID, DepartureDate, ReturnDate, TotalSeats, GuideID) VALUES
(1,  '2026-04-05', '2026-04-05', 20, 1),
(1,  '2026-04-19', '2026-04-19', 20, 1),
(2,  '2026-04-06', '2026-04-06', 25, 2),
(2,  '2026-04-20', '2026-04-20', 25, 2),
(3,  '2026-04-10', '2026-04-11', 15, 3),
(3,  '2026-05-08', '2026-05-09', 15, 3),
(4,  '2026-04-12', '2026-04-12', 20, 1),
(5,  '2026-04-18', '2026-04-20', 12, 2),
(6,  '2026-04-25', '2026-04-25', 20, 1),
(7,  '2026-05-02', '2026-05-03', 16, 3),
(8,  '2026-05-09', '2026-05-10', 18, 2),
(9,  '2026-05-17', '2026-05-17', 25, 1),
(10, '2026-05-23', '2026-05-25', 14, 2);
GO

-- Employees (Admin + Sales + Accounting)
-- PasswordHash: Django make_password('admin1234') — ต้องรัน setup_db.py เพื่อ hash ให้ถูกต้อง
INSERT INTO Employees (FullName, Email, PasswordHash, Role, IsActive) VALUES
(N'Admin System',      'admin@toursongkhla.com',      'admin1234',   'Admin',      1),
(N'สมหญิง ขาย',       'sales@toursongkhla.com',       'sales1234',   'Sales',      1),
(N'บัญชี การเงิน',    'accounting@toursongkhla.com',  'acct1234',    'Accounting', 1);
GO

-- Customers (Seed test account — password: customer1234 hashed with Django make_password)
-- Hash นี้ใช้ bcrypt/pbkdf2 ผ่าน Django's make_password('customer1234')
INSERT INTO Customers (FullName, Email, Phone, Nationality, PasswordHash, CreatedDate) VALUES
(N'Test Customer', 'test@customer.com', '081-999-0001', N'Thai',
 'pbkdf2_sha256$1200000$NFRbdYE8dZZLYqTbbwghtN$fKVzHnMwLLe+jZoZlJ9/5q/4wwMKC78cB3ipy6+l1fo=',
 GETDATE());
GO

PRINT '=== schema.sql completed — TourSongkhla 10 tables + sample data OK ===';
GO
