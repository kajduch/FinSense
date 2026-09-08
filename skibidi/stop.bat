@echo off

taskkill /FI "WINDOWTITLE eq AI Server*" /T /F
taskkill /FI "WINDOWTITLE eq Backend*" /T /F
taskkill /FI "WINDOWTITLE eq Frontend*" /T /F

echo All servers stopped.
pause