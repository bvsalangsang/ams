
"""
SQL Command for ams (API).

List of CRUD functions for ams (API).
"""

def queryGetLogByDate(pdsId, punchDate):

    
    sql = """SELECT punchNo, 
                    eventNo, 
                    empId, 
                    pdsId,
                    employee, 
                    punchDate, 
                    punchTimeIn, 
                    punchTimeOut, 
                    latitude, 
                    longitude, 
                    systemDateTime, 
                    isActive 
                    FROM punch_log 
                    WHERE pdsId =  %s
                    AND punchDate =  %s
                    AND isActive = 'Y'
                    ORDER BY punchNo DESC
                    LIMIT 1
                    """
    
    params = (pdsId, punchDate)

    return sql,params


def queryGetPunchLogByPdsId(pdsId):
    sql = """
            SELECT pch.punchNo, 
            evt.eventName, 
            pch.empId, 
            pch.pdsId,
            pch.employee, 
            pch.punchDate, 
            pch.punchTimeIn, 
            pch.punchTimeOut, 
            pch.latitude, 
            pch.longitude, 
            pch.systemDateTime, 
            pch.isActive 
            FROM punch_log pch
            LEFT JOIN man_event evt ON pch.eventNo = evt.eventNo
            WHERE pch.pdsId =  %s
            AND pch.isActive = 'Y'
            ORDER BY punchNo DESC
                    
         """
    
    params = (pdsId,)
    
    return sql,params


def queryGetSysInfo():
    sql = """SELECT sysId, 
                    function, 
                    sysValue 
                    FROM sys_info 
                    WHERE isActive = 'Y'
                    """
    
    params = ()
    
    return sql,params


def queryGetSchedule():
    sql = """
             SELECT sch.schedId,
                loc.locationId,
                loc.locName,
                evt.eventNo,
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
                WHERE sch.isActive = 'Y' AND isSet = 'Y'
          """
    params = ()
    return sql, params   

def queryGetScheduleByDate(startDate, endDate):    
    sql = """
          SELECT sch.schedId,
                loc.locationId,
                loc.locName,
                evt.eventNo,
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
            AND sch.isSet = 'Y'
            AND (
                    (sch.startDate != '0000-00-00' AND sch.startDate = %s)
                    OR
                    (sch.endDate != '0000-00-00' AND sch.endDate = %s)
                );
            """
    params = (startDate, endDate)

    return sql, params

def queryLocationById(locId):

    sql = """
        SELECT loc.locationId, 
               loc.locName,
               loc.address,
               locDet.longitude,
               locDet.latitude
               FROM man_location loc
               LEFT JOIN man_location_det locDet ON loc.locationId = locDet.locationId
               WHERE loc.isActive = 'Y' AND loc.locationId = %s
        """
    
    params = (locId,)
    
    return sql,params
