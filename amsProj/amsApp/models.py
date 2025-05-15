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


class PunchLog(models.Model):
    punchNo = models.AutoField(primary_key=True, editable=True) 
    shiftNo = models.CharField(max_length=8)
    empId = models.CharField(max_length=20)
    pdsId = models.CharField(max_length=20,null=True)
    employee= models.CharField(max_length=150,null=True)
    punchdate = models.DateField()
    punchTimeIn = models.CharField(max_length=8)
    punchTimeOut = models.CharField(max_length=8)
    latitude  = models.CharField(max_length=30)
    longitude = models.CharField(max_length=30)
    systemDateTime = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    isActive = models.CharField(max_length=1,default='Y')

    class Meta: 
        db_table   = "punch_log"
    
    
    



    

 

   
