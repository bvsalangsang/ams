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

