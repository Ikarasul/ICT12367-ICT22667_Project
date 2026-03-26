-- ==========================================================
-- setup_procedures.sql  ·  TourSongkhla
-- Views + Stored Procedures (ทุกอย่างใช้ TourSchedules/TourPackages)
-- รันหลัง schema.sql
-- ==========================================================

USE TourSongkhla;
GO

-- ----------------------------------------------------------
-- VIEWS
-- ----------------------------------------------------------

-- 1. vw_ScheduleAvailability  (ใช้โดย tours page + booking page)
IF OBJECT_ID('vw_ScheduleAvailability', 'V') IS NOT NULL DROP VIEW vw_ScheduleAvailability;
GO
CREATE VIEW vw_ScheduleAvailability AS
SELECT
    s.ScheduleID,
    ISNULL(t.TourName_en, t.PackageName)        AS TourName,
    ISNULL(t.Destination_en, t.Destination)     AS Destination,
    s.DepartureDate,
    s.ReturnDate,
    s.TotalSeats                                AS Capacity,
    (s.TotalSeats - ISNULL(b.TotalBooked, 0))   AS AvailableSeats,
    t.PricePerPerson                            AS Price,
    s.PackageID                                 AS TourID,
    ISNULL(g.FullName, N'-')                    AS GuideName,
    t.TourName_en,
    t.Destination_en
FROM TourSchedules s
JOIN  TourPackages t ON s.PackageID = t.PackageID
LEFT JOIN Guides   g ON s.GuideID   = g.GuideID
LEFT JOIN (
    SELECT ScheduleID, SUM(NumAdults + ISNULL(NumChildren, 0)) AS TotalBooked
    FROM   Bookings
    WHERE  Status != 'Cancelled'
    GROUP BY ScheduleID
) b ON s.ScheduleID = b.ScheduleID;
GO

-- 2. vw_FlightTickets  (ใช้โดย my_tickets page)
IF OBJECT_ID('vw_FlightTickets', 'V') IS NOT NULL DROP VIEW vw_FlightTickets;
GO
CREATE VIEW vw_FlightTickets AS
SELECT
    b.BookingID,
    b.CustomerID,
    c.FullName                                                              AS CustomerName,
    ISNULL(t.TourName_en, t.PackageName)                                   AS TourName,
    ISNULL(t.Destination_en, t.Destination)                                AS Destination,
    s.DepartureDate,
    s.ReturnDate,
    b.Status,
    b.NumAdults,
    b.NumChildren,
    (b.NumAdults * t.PricePerPerson
     + b.NumChildren * (t.PricePerPerson * 0.5))                           AS TotalPrice,
    ISNULL(g.FullName, N'-')                                               AS GuideName
FROM  Bookings      b
JOIN  Customers     c ON b.CustomerID  = c.CustomerID
JOIN  TourSchedules s ON b.ScheduleID  = s.ScheduleID
JOIN  TourPackages  t ON s.PackageID   = t.PackageID
LEFT JOIN Guides    g ON s.GuideID     = g.GuideID;
GO

-- 3. vw_BookingSummary  (ใช้โดย dashboard)
IF OBJECT_ID('vw_BookingSummary', 'V') IS NOT NULL DROP VIEW vw_BookingSummary;
GO
CREATE VIEW vw_BookingSummary AS
SELECT
    COUNT(BookingID)                                              AS TotalBookings,
    SUM(CASE WHEN Status = 'Pending'    THEN 1 ELSE 0 END)       AS PendingBookings,
    SUM(CASE WHEN Status = 'Confirmed'  THEN 1 ELSE 0 END)       AS ConfirmedBookings,
    SUM(CASE WHEN Status = 'Cancelled'  THEN 1 ELSE 0 END)       AS CancelledBookings
FROM Bookings;
GO

-- 4. vw_AuditLog  (ใช้โดย audit_log page)
IF OBJECT_ID('vw_AuditLog', 'V') IS NOT NULL DROP VIEW vw_AuditLog;
GO
CREATE VIEW vw_AuditLog AS
SELECT
    a.LogID,
    a.TableName,
    a.Action,
    a.PerformedBy,
    ISNULL(e.FullName, CAST(a.PerformedBy AS NVARCHAR)) AS PerformedByName,
    a.Details,
    a.LogDate                                           AS CreatedAt
FROM  AuditLogs a
LEFT JOIN Employees e ON a.PerformedBy = e.EmployeeID;
GO

-- 5. vw_PackageRevenue  (ใช้โดย dashboard — Admin/Accounting)
IF OBJECT_ID('vw_PackageRevenue', 'V') IS NOT NULL DROP VIEW vw_PackageRevenue;
GO
CREATE VIEW vw_PackageRevenue AS
SELECT
    t.PackageID,
    SUM(b.NumAdults * t.PricePerPerson
        + b.NumChildren * (t.PricePerPerson * 0.5))   AS Revenue,
    ISNULL(t.TourName_en, t.PackageName)              AS TourName,
    COUNT(b.BookingID)                                AS BookingCount
FROM  TourPackages  t
JOIN  TourSchedules s ON t.PackageID  = s.PackageID
JOIN  Bookings      b ON s.ScheduleID = b.ScheduleID
WHERE b.Status != 'Cancelled'
GROUP BY t.PackageID, t.TourName_en, t.PackageName;
GO

-- ----------------------------------------------------------
-- STORED PROCEDURES
-- ----------------------------------------------------------

-- sp_Login  (Employee login — plain-text hash comparison)
IF OBJECT_ID('sp_Login', 'P') IS NOT NULL DROP PROCEDURE sp_Login;
GO
CREATE PROCEDURE sp_Login
    @Email        NVARCHAR(255),
    @PasswordHash NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT EmployeeID, FullName, Email, Role, IsActive
    FROM   Employees
    WHERE  Email = @Email
      AND  PasswordHash = @PasswordHash
      AND  IsActive = 1;
END;
GO

-- sp_LoginCustomer  (Customer login — ดึง hash แล้ว check_password() ใน Python)
IF OBJECT_ID('sp_LoginCustomer', 'P') IS NOT NULL DROP PROCEDURE sp_LoginCustomer;
GO
CREATE PROCEDURE sp_LoginCustomer
    @Email NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT CustomerID, FullName, PasswordHash
    FROM   Customers
    WHERE  Email = @Email;
END;
GO

-- sp_RegisterCustomer
IF OBJECT_ID('sp_RegisterCustomer', 'P') IS NOT NULL DROP PROCEDURE sp_RegisterCustomer;
GO
CREATE PROCEDURE sp_RegisterCustomer
    @FullName    NVARCHAR(100),
    @Email       NVARCHAR(255),
    @Phone       NVARCHAR(20),
    @Passport    NVARCHAR(50),
    @DateOfBirth DATE,
    @Nationality NVARCHAR(50),
    @Address     NVARCHAR(MAX),
    @PasswordHash NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM Customers WHERE Email = @Email)
    BEGIN
        RAISERROR(N'Email นี้ถูกใช้งานแล้ว / Email already registered', 16, 1);
        RETURN;
    END
    INSERT INTO Customers
        (FullName, Email, Phone, Passport, DateOfBirth, Nationality, Address, PasswordHash, CreatedDate)
    VALUES
        (@FullName, @Email, @Phone, @Passport, @DateOfBirth, @Nationality, @Address, @PasswordHash, GETDATE());
END;
GO

-- sp_CreateBooking
IF OBJECT_ID('sp_CreateBooking', 'P') IS NOT NULL DROP PROCEDURE sp_CreateBooking;
GO
CREATE PROCEDURE sp_CreateBooking
    @CustomerID  INT,
    @ScheduleID  INT,
    @NumAdults   INT,
    @NumChildren INT
AS
BEGIN
    SET NOCOUNT ON;
    -- ตรวจที่นั่งว่าง
    DECLARE @Available INT;
    SELECT @Available = (TotalSeats - ISNULL(
        (SELECT SUM(NumAdults + ISNULL(NumChildren,0))
         FROM   Bookings
         WHERE  ScheduleID = @ScheduleID AND Status != 'Cancelled'), 0))
    FROM TourSchedules WHERE ScheduleID = @ScheduleID;

    IF @Available IS NULL
    BEGIN
        RAISERROR(N'ไม่พบตารางทัวร์นี้ / Schedule not found', 16, 1); RETURN;
    END
    IF (@NumAdults + ISNULL(@NumChildren,0)) > @Available
    BEGIN
        RAISERROR(N'ที่นั่งไม่เพียงพอ / Not enough seats available', 16, 1); RETURN;
    END

    INSERT INTO Bookings (CustomerID, ScheduleID, NumAdults, NumChildren, BookingDate, Status)
    VALUES (@CustomerID, @ScheduleID, @NumAdults, ISNULL(@NumChildren,0), GETDATE(), 'Pending');

    SELECT SCOPE_IDENTITY() AS NewBookingID;
END;
GO

-- sp_WriteAuditLog
IF OBJECT_ID('sp_WriteAuditLog', 'P') IS NOT NULL DROP PROCEDURE sp_WriteAuditLog;
GO
CREATE PROCEDURE sp_WriteAuditLog
    @TableName   NVARCHAR(100),
    @Action      NVARCHAR(50),
    @PerformedBy INT,
    @Details     NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO AuditLogs (TableName, Action, PerformedBy, Details, LogDate)
    VALUES (@TableName, @Action, @PerformedBy, @Details, GETDATE());
END;
GO

PRINT '=== setup_procedures.sql completed — Views + SPs OK ===';
GO
