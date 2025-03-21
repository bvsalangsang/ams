'-------------------------------------------------------------------------------
'=- Tools  ****
'-------------------------------------------------------------------------------
1. Download visual studio code(v1.85.1)
   - https://code.visualstudio.com/

2. Download python(v3.10.4)
   - https://www.python.org/downloads/  

3. Download xampp
   - https://www.apachefriends.org/index.html

4. Install django (v5.0.6)
  - pip install django

5. install django-cors-headers(v4.3.1)
  - pip install django-cors-headers

6. install django-extensions(v3.2.3)
  - pip install django-extensions

'-------------------------------------------------------------------------------
'=- SETTINGS WEBHOST   ****
'-------------------------------------------------------------------------------
   

'-------------------------------------------------------------------------------
'=- SETTINGS MYSQL  ****
'-------------------------------------------------------------------------------


'-------------------------------------------------------------------------------
'=- extensions VSCODE  ****
'-------------------------------------------------------------------------------


'-------------------------------------------------------------------------------
'=- extensions CHROME  ****
'-------------------------------------------------------------------------------

'-------------------------------------------------------------------------------
'=- Methods  ****
'-------------------------------------------------------------------------------
1. To create virtual environment (vscode)
   - python.exe -m venv <envName> eg:usepmscore

1.a To Install django 
   - pip install Django

2.a To activate vitrual environment (vscode)
   - <envName>\scripts\activate.bat

2.b To deactivate virtual environment (vscode)
   - deactivate

3. create new django project 
  - django-admin startproject <projectName> eg:usepSDGProj 

3.a create startapp 
  - python manage.py startapp <appName> eg:sdgMainApp

4. in settings.py add database details and run command to create admininstration backend:
  - python manage.py migrate


5. Create superuser account
  - python  manage.py createsuperuser 

6. To rearrage columns in MySql
  - ALTER TABLE <table_name> MODIFY <column> char(1) AFTER username 