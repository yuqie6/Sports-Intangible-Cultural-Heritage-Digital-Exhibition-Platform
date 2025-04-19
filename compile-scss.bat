@echo off
chcp 65001 > nul
echo Compiling SCSS files...

REM Check if Sass is installed
sass --version
if %errorlevel% neq 0 (
    echo Error: Sass not found. Please install Sass first:
    echo npm install -g sass
    exit /b 1
)

REM Compile SCSS files
cd heritage_platform\app\static
echo Compiling main.scss to main.css...
sass --no-source-map --verbose scss/main.scss:css/main.css

echo Compilation completed!
pause
