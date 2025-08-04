@echo off
git add .
set /p msg=Mensaje para commit: 
git commit -m "%msg%"
git push
pause