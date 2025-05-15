
"""
SQL Command for ams (API).

List of CRUD functions for ams (API).
"""

def getPunchLogByDate(pdsId, punchDate):

    
    sql = """SELECT punchNo, 
                    shiftNo, 
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

