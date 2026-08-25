@echo off
REM Build script for Image Comparator GUI (Windows)
setlocal enabledelayedexpansion

echo ==========================================
echo Image Comparator - Build Script (Windows)
echo ==========================================
echo.

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Check if script exists
if not exist "image_comparator_gui.py" (
    echo Error: image_comparator_gui.py not found in current directory
    exit /b 1
)

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo Choose build type:
echo 1^) Directory bundle (recommended - faster startup)
echo 2^) Single file (slower startup, easier distribution)
set /p choice="Enter choice (1-2): "

if "%choice%"=="1" (
    echo.
    echo Building directory bundle...
    pyinstaller --windowed ^
        --name="ImageComparator" ^
        --hidden-import=PIL._tkinter_finder ^
        --hidden-import=reportlab.pdfgen.canvas ^
        --hidden-import=pdf2image ^
        image_comparator_gui.py
    
    echo.
    echo Build complete!
    echo Location: dist\ImageComparator\
    echo To distribute: Zip the entire 'dist\ImageComparator' folder
) else if "%choice%"=="2" (
    echo.
    echo Building single file...
    pyinstaller --onefile --windowed ^
        --name="ImageComparator" ^
        --hidden-import=PIL._tkinter_finder ^
        --hidden-import=reportlab.pdfgen.canvas ^
        --hidden-import=pdf2image ^
        image_comparator_gui.py
    
    echo.
    echo Build complete!
    echo Location: dist\ImageComparator.exe
    echo To distribute: Share the single .exe file
) else (
    echo Invalid choice
    exit /b 1
)

echo.
echo Testing the build...
if exist "dist\ImageComparator.exe" (
    echo    Executable found: dist\ImageComparator.exe
) else if exist "dist\ImageComparator\" (
    echo    Bundle found: dist\ImageComparator\
)

echo.
echo ==========================================
echo Build process complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Test the executable on your machine
echo 2. Test on a clean machine without Python
echo 3. Distribute to users
echo.
echo Note: Users may need poppler for PDF support
echo Download from: https://github.com/oschwartz10612/poppler-windows/releases
echo.

pause
