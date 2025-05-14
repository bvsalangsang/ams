
"""
SQL Command for ams (API).

List of CRUD functions for ams (API).
"""

def getPunchLogByDate(empId, punchDate):
    
    sql = """SELECT punchNo, 
                    shiftNo, 
                    empId, 
                    employee, 
                    punchDate, 
                    punchTimeIn, 
                    punchTimeOut, 
                    latitude, 
                    longitude, 
                    systemDateTime, 
                    isActive 
                    FROM punch_log 
                    WHERE empId =  %s
                    AND punchDate =  %s
                    ORDER BY punchNo DESC
                    LIMIT 1
                    """
    
    params = (empId, punchDate)

    return sql,params

