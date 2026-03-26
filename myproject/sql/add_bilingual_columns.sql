

USE TourSongkhla;
GO

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'TourPackages' AND COLUMN_NAME = 'TourName_en'
)
BEGIN
    ALTER TABLE TourPackages ADD TourName_en NVARCHAR(255) NULL;
    PRINT 'Added TourName_en';
END
ELSE PRINT 'TourName_en already exists';

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'TourPackages' AND COLUMN_NAME = 'Destination_en'
)
BEGIN
    ALTER TABLE TourPackages ADD Destination_en NVARCHAR(255) NULL;
    PRINT 'Added Destination_en';
END
ELSE PRINT 'Destination_en already exists';
GO


UPDATE TourPackages SET TourName_en = 'Japan Tokyo 5 Days',      Destination_en = 'Tokyo, Japan'         WHERE PackageName LIKE N'%ญี่ปุ่น%';
UPDATE TourPackages SET TourName_en = 'Korea Seoul 4 Days',      Destination_en = 'Seoul, Korea'         WHERE PackageName LIKE N'%เกาหลี%';
UPDATE TourPackages SET TourName_en = 'Europe Tour 8 Days',      Destination_en = 'Paris, France'        WHERE PackageName LIKE N'%ยุโรป%';
UPDATE TourPackages SET TourName_en = 'China Beijing 6 Days',    Destination_en = 'Beijing, China'       WHERE PackageName LIKE N'%จีน%';
UPDATE TourPackages SET TourName_en = 'Singapore 3 Days',        Destination_en = 'Singapore'            WHERE PackageName LIKE N'%สิงคโปร์%';
UPDATE TourPackages SET TourName_en = 'Chiang Mai North Tour',   Destination_en = 'Chiang Mai, Thailand' WHERE PackageName LIKE N'%เชียงใหม่%';
UPDATE TourPackages SET TourName_en = 'Phuket Beach Tour',       Destination_en = 'Phuket, Thailand'     WHERE PackageName LIKE N'%ภูเก็ต%';
UPDATE TourPackages SET TourName_en = 'Krabi Island Tour',       Destination_en = 'Krabi, Thailand'      WHERE PackageName LIKE N'%กระบี่%';
UPDATE TourPackages SET TourName_en = 'Vietnam Hanoi 5 Days',    Destination_en = 'Hanoi, Vietnam'       WHERE PackageName LIKE N'%เวียดนาม%';
UPDATE TourPackages SET TourName_en = 'Taiwan Taipei 4 Days',    Destination_en = 'Taipei, Taiwan'       WHERE PackageName LIKE N'%ไต้หวัน%';
PRINT 'Updated bilingual data';
GO

IF OBJECT_ID('vw_ScheduleAvailability', 'V') IS NOT NULL
    DROP VIEW vw_ScheduleAvailability;
GO

CREATE VIEW vw_ScheduleAvailability AS
SELECT
    s.ScheduleID,                                                        
    t.PackageName                         AS TourName,                   
    t.Destination,                                                       
    s.DepartureDate,                                                     
    s.ReturnDate,                                                        
    s.TotalSeats                          AS Capacity,                  
    (s.TotalSeats - ISNULL(b.TotalBooked, 0)) AS AvailableSeats,        
    t.PricePerPerson                      AS Price,                    
    s.PackageID                           AS TourID,                     
    ISNULL(g.FullName, '-')               AS GuideName,                 
    ISNULL(t.TourName_en, t.PackageName)       AS TourName_en,           
    ISNULL(t.Destination_en, t.Destination)    AS Destination_en         
FROM TourSchedules s
JOIN TourPackages t ON s.PackageID = t.PackageID
LEFT JOIN Guides g ON s.GuideID = g.GuideID
LEFT JOIN (
    SELECT ScheduleID, SUM(NumAdults + ISNULL(NumChildren, 0)) AS TotalBooked
    FROM Bookings
    WHERE Status != 'Cancelled'
    GROUP BY ScheduleID
) b ON s.ScheduleID = b.ScheduleID;
GO

PRINT 'View vw_ScheduleAvailability created successfully!';
GO

SELECT TOP 5 * FROM vw_ScheduleAvailability;
GO
