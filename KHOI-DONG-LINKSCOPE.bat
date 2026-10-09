@echo off
setlocal
cd /d "%~dp0"
title LinkScope - Khoi dong tool

echo ====================================================
echo   LINKSCOPE - GIA, HOA HONG VA LICH SU SHOPEE
echo ====================================================
echo.

if not exist "launch.py" goto :missing_files
if not exist "app.py" goto :missing_files
if not exist "requirements.txt" goto :missing_files

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
    goto :run
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    goto :run
)

echo Chua tim thay Python 3.10 tro len.
echo Hay cai Python tu trang chinh thuc dang duoc mo.
echo Khi cai, tick "Add python.exe to PATH" neu co.
echo Sau khi cai xong, nhap dup file nay lan nua.
start "" "https://www.python.org/downloads/windows/"
pause
exit /b 1

:missing_files
echo Thieu file chuong trinh.
echo Hay giai nen TOAN BO file ZIP vao mot thu muc rieng.
echo Khong chay file BAT truc tiep ben trong ZIP.
pause
exit /b 1

:run
%PY_CMD% launch.py
if errorlevel 1 (
    echo.
    echo Tool chua khoi dong thanh cong. Xem thong bao loi phia tren.
    echo Ban co the chup man hinh loi de duoc ho tro. Khong de lo API Key.
    pause
    exit /b 1
)
endlocal
