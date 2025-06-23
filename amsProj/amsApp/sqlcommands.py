"""
SQL Command for amsApp.

List of CRUD functions for amsApp 
"""

#attendance Logs
def fetchAttLogs():
   sql = ("""
        SELECT * from punch_log WHERE isActive = 'Y'
         """)
   
   return sql

def fecthAttendanceLogs():
    sql = """
        SELECT pch.punchNo, 
               evt.eventName, 
               pch.empId, 
               pch.pdsId,
               pch.employee, 
               pch.office,
               pch.punchDate, 
               pch.punchTimeIn, 
               pch.punchTimeOut, 
               pch.latitude, 
               pch.longitude, 
               pch.systemDateTime, 
               pch.isActive
              FROM punch_log pch
              LEFT JOIN man_event evt ON pch.eventNo = evt.eventNo
              WHERE pch.isActive = 'Y'
              ORDER BY pch.punchNo DESC
          """
    return sql

def fetchAttendanceLogsByDateRange():
    sql = """
        SELECT pch.punchNo, 
               evt.eventName, 
               pch.empId, 
               pch.pdsId,
               pch.employee, 
               pch.office,
               pch.punchDate, 
               pch.punchTimeIn, 
               pch.punchTimeOut, 
               pch.latitude, 
               pch.longitude, 
               pch.officeId,
               pch.systemDateTime, 
               pch.isActive
          FROM punch_log pch
          LEFT JOIN man_event evt ON pch.eventNo = evt.eventNo
         WHERE pch.isActive = 'Y'
           AND pch.punchDate BETWEEN %s AND %s
         ORDER BY pch.punchNo DESC
    """
    return sql

#shift
def fetchShift():
   sql = ("""
     SELECT * FROM man_shift WHERE isActive = 'Y'
    """)
   return sql 

def saveUpdateShift():
    sql = """
        INSERT INTO man_shift (shiftNo, shiftName, shiftTypeNo, breakNo, description, startTime, endTime, isActive)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        shiftName = VALUES(shiftName),
        shiftTypeNo = VALUES(shiftTypeNo),
        breakNo = VALUES(breakNo),
        description = VALUES(description),
        startTime = VALUES(startTime),
        endTime = VALUES(endTime),
        isActive = VALUES(isActive)
    """
    return sql 

def deleteShift():
    sql = "UPDATE man_shift SET isActive = 'N' WHERE  shiftNo = %s"
    return sql  

def fetchShiftType():
   sql = ("""

     SELECT * FROM man_shift_type WHERE isActive = 'Y'

      """)

   return sql     

def saveUpdateShiftType():
    sql = """
        INSERT INTO man_shift_type (shiftTypeNo, shiftType, isActive)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        shiftType = VALUES(shiftType),
        isActive = VALUES(isActive)
    """
    return sql 


def deleteSQueryShiftType():
    sql = "UPDATE man_shift_type SET isActive = 'N' WHERE  shiftTypeNo = %s"
    return sql  

#event 
def fetchQueryEvent():  
    sql = ("""
        SELECT man_event.eventNo , 
              man_event.eventName, 
              man_event_type.eventType, 
              man_event.description,
              man_event.isActive
              FROM  man_event 
              LEFT JOIN man_event_type ON man_event.eventTypeNo = man_event_type.eventTypeNo
           WHERE man_event.isActive = 'Y'
       """)
    return sql

def saveUpdateQueryEvent():
    sql = """     
        INSERT INTO man_event (eventNo, eventName, eventTypeNo, description, isActive)        
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        eventName = VALUES(eventName),
        eventTypeNo = VALUES(eventTypeNo),  
        description = VALUES(description),
        isActive = VALUES(isActive)
        """
    return sql

def delQueryEvent():
    sql = """
        UPDATE man_event set isActive = 'N' WHERE eventNo = %s  
        
        """
    return sql

#event type
def fetchQueryEventType():
    sql = """
        SELECT * FROM man_event_type WHERE isActive = 'Y'
        """
    return sql 

def saveUpdateQueryEventType():
    sql = """    
        INSERT INTO man_event_type (eventTypeNo, eventType, isActive)        
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        eventType = VALUES(eventType),
        isActive = VALUES(isActive)
          """
    
    return sql

def delQueryEventType():
    sql = """
        UPDATE man_event_type set isActive = 'N' WHERE eventTypeNo = %s  
        
        """
    return sql

#location   
def fetchQueryLocation():
    sql = """
        SELECT loc.locationId, 
               loc.locName,
               loc.address,
               loc.isActive,
               locDet.longitude,
               locDet.latitude
               FROM man_location loc
               LEFT JOIN man_location_det locDet ON loc.locationId = locDet.locationId
               WHERE loc.isActive = 'Y'
        """
    return sql

def fetchQueryLocationOnly():
    sql= """
        SELECT * from man_location WHERE isActive = 'Y'
     
         """
    return sql

def saveUpdateQueryLocation():
    sql = """
        INSERT INTO man_location (locationId, locName, address, isActive)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        locName = VALUES(locName),
        address = VALUES(address),
        isActive = VALUES(isActive)
    """
    return sql

        
def saveQueryLocationDet():
    sql = """
        INSERT INTO man_location_det (locationId, longitude, latitude, isActive)
        VALUES (%s, %s, %s, %s)
        """
    return sql



#schedule
def fetchQuerySchedule():
    sql = """
            SELECT sch.schedId,
                loc.locName,
                evt.eventName,
                sch.startDate,
                sch.endDate,
                sch.startTime,
                sch.startGrace,
                sch.endTime,
                sch.endGrace,
                sch.recurrenceType,
                sch.recurrenceDays,
                sch.dateCreated,
                sch.isRecurring,
                sch.isSet,
                sch.isActive
                FROM schedule sch
                LEFT JOIN man_location loc ON sch.locationId = loc.locationId
                LEFT JOIN man_event evt ON sch.eventNo = evt.eventNo
                WHERE sch.isActive = 'Y'
            """
    return sql

def saveUpdateQuerySchedule():
    sql = """
        INSERT INTO schedule (schedId, locationId, eventNo, startDate, 
                             endDate, startTime, startGrace, 
                             endTime, endGrace, recurrenceType, 
                             recurrenceDays,
                             isRecurring,isSet, isActive)      

        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        locationId = VALUES(locationId),
        eventNo = VALUES(eventNo),
        startDate = VALUES(startDate),
        endDate = VALUES(endDate), 
        startTime = VALUES(startTime),
        startGrace = VALUES(startGrace),
        endTime = VALUES(endTime),
        endGrace = VALUES(endGrace),
        recurrenceType = VALUES(recurrenceType),
        recurrenceDays = VALUES(recurrenceDays),
        isRecurring = VALUES(isRecurring),
        isSet = VALUES(isSet),
        isActive = VALUES(isActive)
      """
    return sql

def delQuerySchedule():
    sql = """
        UPDATE schedule set isActive = 'N' WHERE schedId = %s  
        
        """
    return sql  

#set Schedule

def setQuerySchedule():
    sql = """
        UPDATE schedule set isSet = %s WHERE schedId = %s  
        
        """
    return sql  
