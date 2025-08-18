from django.db import models

# Create your models here.
class ManShift(models.Model):
   shiftNo = models.AutoField(primary_key=True, editable=True)
   shiftName = models.CharField(max_length=200)
   shiftTypeNo = models.CharField(max_length=2)
   breakNo  = models.CharField(max_length=2)
   description = models.CharField(max_length=500)
   startTime  = models.CharField(max_length=8)
   endTime = models.CharField(max_length=8)
   isActive = models.CharField(max_length=1, default='Y')

   class Meta: 
        db_table = "man_shift"

class ManShiftType(models.Model):
    shiftTypeNo = models.AutoField(primary_key=True, editable=True)
    shiftType = models.CharField(max_length=50)
    isActive = models.CharField(max_length=1, default='Y')

    class Meta: 
        db_table = "man_shift_type"

class ManShiftBreak(models.Model):
   breakNo = models.AutoField(primary_key=True, editable=True)
   breakName = models.CharField(max_length=50)
   description = models.CharField(max_length=500)
   startTime = models.CharField(max_length=8)
   endTime = models.CharField(max_length=8)
   isActive = models.CharField(max_length=1, default='Y')

   class Meta:
        db_table = "man_shift_break"

# punch log
class PunchLog(models.Model):
    punchNo = models.AutoField(primary_key=True, editable=True) 
    eventNo = models.CharField(max_length=8)
    locationId = models.CharField(max_length=10, null=True, blank=True)
    empId = models.CharField(max_length=20)
    pdsId = models.CharField(max_length=20,null=True)
    employee= models.CharField(max_length=150,null=True)
    punchdate = models.DateField()
    punchTimeIn = models.CharField(max_length=8)
    punchTimeOut = models.CharField(max_length=8)
    latitude  = models.CharField(max_length=30)
    longitude = models.CharField(max_length=30)
    officeId = models.CharField(max_length=10, null=True, blank=True)
    office = models.CharField(max_length=400, null=True, blank=True)
    # systemDateTime = models.DateTimeField(null=True, blank=True)
    isActive = models.CharField(max_length=1,default='Y')

    class Meta: 
        db_table   = "punch_log"
    
class PunchLogTamper(models.Model):
        tamperNo = models.AutoField(primary_key=True, editable=True) 
        eventNo = models.CharField(max_length=8)
        locationId = models.CharField(max_length=10, null=True, blank=True)
        empId = models.CharField(max_length=20)
        pdsId = models.CharField(max_length=20,null=True)
        employee= models.CharField(max_length=150,null=True)
        punchdate = models.DateField()
        punchTimeIn = models.CharField(max_length=8)
        punchTimeOut = models.CharField(max_length=8)
        latitude  = models.CharField(max_length=30)
        longitude = models.CharField(max_length=30)
        officeId = models.CharField(max_length=10, null=True, blank=True)
        office = models.CharField(max_length=400, null=True, blank=True)
        #systemDateTime = models.DateTimeField(null=True, blank=True)
        isActive = models.CharField(max_length=1,default='Y')

        class Meta: 
            db_table   = "punch_log_tamper"

class EvaluatedPunchLog(models.Model):
    evalPunchNo = models.AutoField(primary_key=True, editable=True) 
    punchNo = models.CharField(max_length=10)
    eventNo = models.CharField(max_length=8)
    locationId = models.CharField(max_length=10, null=True, blank=True)
    empId = models.CharField(max_length=20)
    pdsId = models.CharField(max_length=20,null=True)
    employee= models.CharField(max_length=150,null=True)
    empStatus = models.CharField(max_length=50)
    empType = models.CharField(max_length=30)
    empRank = models.CharField(max_length=200)
    punchdate = models.DateField()
    punchTimeIn = models.CharField(max_length=8)
    punchTimeOut = models.CharField(max_length=8)
    latitude  = models.CharField(max_length=30)
    longitude = models.CharField(max_length=30)
    officeId = models.CharField(max_length=10, null=True, blank=True)
    office = models.CharField(max_length=400, null=True, blank=True)
    campusId = models.CharField(max_length=8)
    campus = models.CharField(max_length=30)
    systemDateTime = models.DateTimeField(null=True, blank=True)  # ✅ Add this back
    attStatusId = models.CharField(max_length=1)
    remarks = models.CharField(max_length=500, null=True, blank=True)
    isActive = models.CharField(max_length=1,default='Y')

    class Meta: 
        db_table   = "punch_log_eval"

class sysInfo(models.Model):
    sysId = models.AutoField(primary_key=True, editable=True)
    function = models.CharField(max_length=50)
    sysValue = models.CharField(max_length=50)

    class Meta: 
        db_table   = "sys_info"

#event
class ManEvent(models.Model):
   eventNo = models.AutoField(primary_key=True, editable=True)
   eventName = models.CharField(max_length=200)
   eventTypeNo = models.CharField(max_length=2)
   description = models.CharField(max_length=500)
   isActive = models.CharField(max_length=1, default='Y')

   class Meta: 
        db_table = "man_event"

class ManEventType(models.Model):
    eventTypeNo = models.AutoField(primary_key=True, editable=True)
    eventType = models.CharField(max_length=50)
    isActive = models.CharField(max_length=1, default='Y')

    class Meta: 
        db_table = "man_event_type"

#location  
class ManLocation(models.Model):
    locationId = models.AutoField(primary_key=True,editable=True)
    locName = models.CharField(max_length=100)
    address = models.CharField(max_length=500)
    isActive = models.CharField(max_length=1, default='Y')

    class Meta:
        db_table = "man_location"
   
class ManLocationDet(models.Model):
    ctrlNo = models.AutoField(primary_key=True,editable=True)
    locationId = models.CharField(max_length=10)
    longitude = models.CharField (max_length=15)
    latitude = models.CharField(max_length=15)
    isActive = models.CharField(max_length=1, default='Y')

    class Meta: 
        db_table = "man_location_det"

#schedule
class ManSchedule(models.Model):
    schedId = models.AutoField(primary_key=True)
    locationId = models.CharField(max_length=5, null=True, blank=True)
    eventNo = models.CharField(max_length=10)
    startDate = models.DateField(null=True, blank=True)
    endDate = models.DateField(null=True, blank=True)
    startTime = models.CharField(max_length=8)
    startGrace = models.CharField(max_length=8)
    endTime = models.CharField(max_length=8)
    endGrace = models.CharField(max_length=8)
    recurrenceType = models.CharField(max_length=20, null=True, blank=True)
    recurrenceDays = models.CharField(max_length=150, null=True, blank=True)
    dateCreated = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    isRecurring = models.CharField(max_length=1, default='N')
    isSet = models.CharField(max_length=1, default='N')
    isActive = models.CharField(max_length=1, default='Y')

    class Meta:
        db_table = "schedule"

class CancelledSchedule(models.Model):
    cancelledId = models.AutoField(primary_key=True)
    schedId = models.CharField(max_length=10)
    cancelledDate = models.DateField()
    reason = models.TextField(null=True, blank=True)  # e.g., "Heavy Rain"
    cancelledBy = models.CharField(max_length=100, null=True, blank=True)  
    dateTimeCreated = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cancelled_schedule"

# evaluation status
class SysPunchStatus(models.Model):
    sysEvalId = models.AutoField(primary_key=True)
    punchName = models.CharField(max_length=20)
    punchLastPkey = models.CharField(max_length=20)
    punchLastDate = models.DateField(null=True, blank=True)
    punchCount = models.CharField(max_length=20)
    lastUpdated = models.DateTimeField(auto_now=True)
    isActive = models.CharField(max_length=1, default='Y')    

    class Meta: 
        db_table = "sys_punch"

class DashUsers(models.Model):
    empId = models.CharField(max_length=20, primary_key=True)
    pdsId = models.CharField(max_length=20, null=True, blank=True)
    employee = models.CharField(max_length=150, null=True, blank=True)
    dateCreated = models.DateTimeField(auto_now_add=True) 
    isActive = models.CharField(max_length=1, default='Y')    
    
    class Meta:
        db_table = "dash_users"