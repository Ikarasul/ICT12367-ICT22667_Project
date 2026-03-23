-- ==========================================================
-- setup_procedures.sql
-- รวม Script สร้าง Views และ Stored Procedures ของระบบ
-- ให้รันใน SQL Server (SSMS หรือ Azure Data Studio)
-- ==========================================================

-- 1. Views
-- ----------------------------------------------------------

-- vw_ScheduleAvailability
IF OBJECT_ID('vw_ScheduleAvailability', 'V') IS NOT NULL DROP VIEW vw_ScheduleAvailability;
GO
CREATE VIEW vw_ScheduleAvailability AS
SELECT 
    s.ScheduleID,
    t.TourName,
    t.Destination,
    s.DepartureDate,
    s.ReturnDate,
    s.Capacity,
    (s.Capacity - ISNULL(b.TotalBooked, 0)) AS AvailableSeats,
    t.Price,
    s.TourID,
    s.GuideName
FROM Schedules s
JOIN Tours t ON s.TourID = t.TourID
LEFT JOIN (
    SELECT ScheduleID, SUM(NumAdults + NumChildren) AS TotalBooked
    FROM Bookings
    WHERE Status != 'Cancelled'
    GROUP BY ScheduleID
) b ON s.ScheduleID = b.ScheduleID;
GO

-- vw_FlightTickets
IF OBJECT_ID('vw_FlightTickets', 'V') IS NOT NULL DROP VIEW vw_FlightTickets;
GO
CREATE VIEW vw_FlightTickets AS
SELECT 
    b.BookingID,
    c.CustomerID,
    c.FullName AS CustomerName,
    t.TourName,
    t.Destination,
    s.DepartureDate,
    s.ReturnDate,
    b.Status,
    b.NumAdults,
    b.NumChildren,
    (b.NumAdults * t.Price + b.NumChildren * (t.Price * 0.5)) AS TotalPrice,
    s.GuideName
FROM Bookings b
JOIN Customers c ON b.CustomerID = c.CustomerID
JOIN Schedules s ON b.ScheduleID = s.ScheduleID
JOIN Tours t ON s.TourID = t.TourID;
GO

-- vw_BookingSummary
IF OBJECT_ID('vw_BookingSummary', 'V') IS NOT NULL DROP VIEW vw_BookingSummary;
GO
CREATE VIEW vw_BookingSummary AS
SELECT 
    COUNT(BookingID) AS TotalBookings,
    SUM(CASE WHEN Status = 'Pending' THEN 1 ELSE 0 END) AS PendingBookings,
    SUM(CASE WHEN Status = 'Confirmed' THEN 1 ELSE 0 END) AS ConfirmedBookings,
    SUM(CASE WHEN Status = 'Cancelled' THEN 1 ELSE 0 END) AS CancelledBookings
FROM Bookings;
GO

-- 2. Stored Procedures
-- ----------------------------------------------------------

-- sp_Login
IF OBJECT_ID('sp_Login', 'P') IS NOT NULL DROP PROCEDURE sp_Login;
GO
CREATE PROCEDURE sp_Login
    @Email NVARCHAR(255),
    @PasswordHash NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT EmployeeID, FullName, Email, Role, IsActive
    FROM Employees
    WHERE Email = @Email AND PasswordHash = @PasswordHash AND IsActive = 1;
END;
GO

-- sp_LoginCustomer
IF OBJECT_ID('sp_LoginCustomer', 'P') IS NOT NULL DROP PROCEDURE sp_LoginCustomer;
GO
CREATE PROCEDURE sp_LoginCustomer
    @Email NVARCHAR(255),
    @PasswordHash NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT CustomerID, FullName, Email
    FROM Customers
    WHERE Email = @Email AND PasswordHash = @PasswordHash;
END;
GO

-- sp_RegisterCustomer
IF OBJECT_ID('sp_RegisterCustomer', 'P') IS NOT NULL DROP PROCEDURE sp_RegisterCustomer;
GO
CREATE PROCEDURE sp_RegisterCustomer
    @FullName NVARCHAR(100),
    @Email NVARCHAR(255),
    @Phone NVARCHAR(20),
    @Passport NVARCHAR(50),
    @DateOfBirth DATE,
    @Nationality NVARCHAR(50),
    @Address NVARCHAR(MAX),
    @PasswordHash NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Customers (FullName, Email, Phone, Passport, DateOfBirth, Nationality, Address, PasswordHash, CreatedDate)
    VALUES (@FullName, @Email, @Phone, @Passport, @DateOfBirth, @Nationality, @Address, @PasswordHash, GETDATE());
END;
GO

-- sp_CreateBooking
IF OBJECT_ID('sp_CreateBooking', 'P') IS NOT NULL DROP PROCEDURE sp_CreateBooking;
GO
CREATE PROCEDURE sp_CreateBooking
    @CustomerID INT,
    @ScheduleID INT,
    @NumAdults INT,
    @NumChildren INT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Bookings (CustomerID, ScheduleID, NumAdults, NumChildren, BookingDate, Status)
    VALUES (@CustomerID, @ScheduleID, @NumAdults, @NumChildren, GETDATE(), 'Pending');
END;
GO

-- sp_WriteAuditLog
IF OBJECT_ID('sp_WriteAuditLog', 'P') IS NOT NULL DROP PROCEDURE sp_WriteAuditLog;
GO
CREATE PROCEDURE sp_WriteAuditLog
    @TableName NVARCHAR(100),
    @Action NVARCHAR(50),
    @PerformedBy INT,
    @Details NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO AuditLogs (TableName, Action, PerformedBy, Details, LogDate)
    VALUES (@TableName, @Action, @PerformedBy, @Details, GETDATE());
END;
GO
