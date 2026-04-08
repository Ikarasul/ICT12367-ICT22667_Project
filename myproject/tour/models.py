# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Auditlog(models.Model):
    logid = models.AutoField(db_column='LogID', primary_key=True)  # Field name made lowercase.
    tablename = models.CharField(db_column='TableName', max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    operation = models.CharField(db_column='Operation', max_length=10, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    recordid = models.IntegerField(db_column='RecordID', blank=True, null=True)  # Field name made lowercase.
    changedby = models.CharField(db_column='ChangedBy', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    changedescription = models.TextField(db_column='ChangeDescription', db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    changetimestamp = models.DateTimeField(db_column='ChangeTimestamp', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AuditLog'


class Auditlogs(models.Model):
    logid = models.AutoField(db_column='LogID', primary_key=True)  # Field name made lowercase.
    tablename = models.CharField(db_column='TableName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    action = models.CharField(db_column='Action', max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    performedby = models.IntegerField(db_column='PerformedBy', blank=True, null=True)  # Field name made lowercase.
    details = models.TextField(db_column='Details', db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    logdate = models.DateTimeField(db_column='LogDate')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AuditLogs'


class Bookings(models.Model):
    bookingid = models.AutoField(db_column='BookingID', primary_key=True)  # Field name made lowercase.
    customerid = models.ForeignKey('Customers', models.DO_NOTHING, db_column='CustomerID')  # Field name made lowercase.
    scheduleid = models.ForeignKey('Tourschedules', models.DO_NOTHING, db_column='ScheduleID')  # Field name made lowercase.
    numadults = models.IntegerField(db_column='NumAdults')  # Field name made lowercase.
    numchildren = models.IntegerField(db_column='NumChildren')  # Field name made lowercase.
    bookingdate = models.DateTimeField(db_column='BookingDate')  # Field name made lowercase.
    status = models.CharField(db_column='Status', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Bookings'


class Customers(models.Model):
    customerid = models.AutoField(db_column='CustomerID', primary_key=True)  # Field name made lowercase.
    fullname = models.CharField(db_column='FullName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    email = models.CharField(db_column='Email', unique=True, max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    phone = models.CharField(db_column='Phone', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    passport = models.CharField(db_column='Passport', max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    dateofbirth = models.DateField(db_column='DateOfBirth', blank=True, null=True)  # Field name made lowercase.
    nationality = models.CharField(db_column='Nationality', max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    address = models.TextField(db_column='Address', db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    passwordhash = models.CharField(db_column='PasswordHash', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Customers'


class Employees(models.Model):
    employeeid = models.AutoField(db_column='EmployeeID', primary_key=True)  # Field name made lowercase.
    fullname = models.CharField(db_column='FullName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    email = models.CharField(db_column='Email', unique=True, max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    passwordhash = models.CharField(db_column='PasswordHash', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    role = models.CharField(db_column='Role', max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    isactive = models.BooleanField(db_column='IsActive')  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Employees'


class Guides(models.Model):
    guideid = models.AutoField(db_column='GuideID', primary_key=True)  # Field name made lowercase.
    fullname = models.CharField(db_column='FullName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    phone = models.CharField(db_column='Phone', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    languages = models.CharField(db_column='Languages', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    isactive = models.BooleanField(db_column='IsActive')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Guides'


class Hotels(models.Model):
    hotelid = models.AutoField(db_column='HotelID', primary_key=True)  # Field name made lowercase.
    hotelname = models.CharField(db_column='HotelName', max_length=200, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    location = models.CharField(db_column='Location', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    starrating = models.SmallIntegerField(db_column='StarRating', blank=True, null=True)  # Field name made lowercase.
    pricepernight = models.DecimalField(db_column='PricePerNight', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Hotels'


class Payments(models.Model):
    paymentid = models.AutoField(db_column='PaymentID', primary_key=True)  # Field name made lowercase.
    bookingid = models.ForeignKey(Bookings, models.DO_NOTHING, db_column='BookingID')  # Field name made lowercase.
    amount = models.DecimalField(db_column='Amount', max_digits=12, decimal_places=2)  # Field name made lowercase.
    paymentdate = models.DateTimeField(db_column='PaymentDate')  # Field name made lowercase.
    paymentmethod = models.CharField(db_column='PaymentMethod', max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='Status', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Payments'


class Tourpackages(models.Model):
    packageid = models.AutoField(db_column='PackageID', primary_key=True)  # Field name made lowercase.
    packagename = models.CharField(db_column='PackageName', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    tourname_en = models.CharField(db_column='TourName_en', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    destination = models.CharField(db_column='Destination', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    destination_en = models.CharField(db_column='Destination_en', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    priceperperson = models.DecimalField(db_column='PricePerPerson', max_digits=10, decimal_places=2)  # Field name made lowercase.
    description = models.TextField(db_column='Description', db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    imageurl = models.CharField(db_column='ImageURL', max_length=500, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    durationdays = models.IntegerField(db_column='DurationDays', blank=True, null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'TourPackages'


class Tourschedules(models.Model):
    scheduleid = models.AutoField(db_column='ScheduleID', primary_key=True)  # Field name made lowercase.
    packageid = models.ForeignKey(Tourpackages, models.DO_NOTHING, db_column='PackageID')  # Field name made lowercase.
    departuredate = models.DateField(db_column='DepartureDate')  # Field name made lowercase.
    returndate = models.DateField(db_column='ReturnDate')  # Field name made lowercase.
    totalseats = models.IntegerField(db_column='TotalSeats')  # Field name made lowercase.
    guideid = models.ForeignKey(Guides, models.DO_NOTHING, db_column='GuideID', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'TourSchedules'


class Vehicles(models.Model):
    vehicleid = models.AutoField(db_column='VehicleID', primary_key=True)  # Field name made lowercase.
    vehicletype = models.CharField(db_column='VehicleType', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    capacity = models.IntegerField(db_column='Capacity', blank=True, null=True)  # Field name made lowercase.
    platenumber = models.CharField(db_column='PlateNumber', max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Vehicles'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150, db_collation='SQL_Latin1_General_CP1_CI_AS')

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128, db_collation='SQL_Latin1_General_CP1_CI_AS')
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150, db_collation='SQL_Latin1_General_CP1_CI_AS')
    first_name = models.CharField(max_length=150, db_collation='SQL_Latin1_General_CP1_CI_AS')
    last_name = models.CharField(max_length=150, db_collation='SQL_Latin1_General_CP1_CI_AS')
    email = models.CharField(max_length=254, db_collation='SQL_Latin1_General_CP1_CI_AS')
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    object_repr = models.CharField(max_length=200, db_collation='SQL_Latin1_General_CP1_CI_AS')
    action_flag = models.SmallIntegerField()
    change_message = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS')
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')
    model = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')
    name = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40, db_collation='SQL_Latin1_General_CP1_CI_AS')
    session_data = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS')
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Sysdiagrams(models.Model):
    name = models.CharField(max_length=128, db_collation='SQL_Latin1_General_CP1_CI_AS')
    principal_id = models.IntegerField()
    diagram_id = models.AutoField(primary_key=True)
    version = models.IntegerField(blank=True, null=True)
    definition = models.BinaryField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sysdiagrams'
        unique_together = (('principal_id', 'name'),)


class TourBooking(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer_name = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')
    customer_email = models.CharField(max_length=254, db_collation='SQL_Latin1_General_CP1_CI_AS')
    customer_phone = models.CharField(max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS')
    booking_date = models.DateField()
    adult_count = models.IntegerField()
    child_count = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS')
    time_slot = models.ForeignKey('TourTimeslot', models.DO_NOTHING)
    tour = models.ForeignKey('TourTour', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'tour_booking'


class TourTimeslot(models.Model):
    id = models.BigAutoField(primary_key=True)
    time = models.TimeField()
    tour = models.ForeignKey('TourTour', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'tour_timeslot'


class TourTour(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')
    description = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS')
    price_adult = models.DecimalField(max_digits=10, decimal_places=2)
    price_child = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS')
    category = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS')
    image = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tour_tour'
