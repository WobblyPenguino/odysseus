@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo start_windows_assistant.bat now delegates to the recommended Nova v55.3.161 START HERE launcher.
rem start_nova_best_models.bat is the delegated better-model launcher behind START_NOVA_HERE.bat
rem Preserve legacy desktop voice listener contract: NOVA_START_CHOICE=2 means Browser UI mode.
rem Preserve Orbit web UI cache-busting contract: nova_ui=v55.3.147
if "%NOVA_START_CHOICE%"=="2" echo NOVA_START_CHOICE=2 detected; launching Browser UI through START_NOVA_HERE.bat.
rem Legacy dependency_check marker: python -m winlocalassistant.dependency_check
rem Install missing Python packages when required; Continue anyway is handled by START_NOVA_HERE.bat.

if "%NOVA_SKIP_STARTUP_TESTS%"=="1" goto startup_validation_skipped
echo Running Nova startup validation gate...
py -3 -m winlocalassistant.startup_validation --mode quick --root "%~dp0" --timeout 90
if errorlevel 1 goto startup_validation_failed
goto startup_validation_done

:startup_validation_failed
echo Nova startup validation failed. Check the report before treating this launch as release-clean.
set /p NOVA_CONTINUE=Continue anyway for debugging? [y/N] 
if /I not "%NOVA_CONTINUE%"=="Y" exit /b 1
goto startup_validation_done

:startup_validation_skipped
echo NOVA_SKIP_STARTUP_TESTS is set; skipping startup validation.

:startup_validation_done
rem Run Nova full system test
rem winlocalassistant.nova_system_test
rem http://127.0.0.1:8766
rem Browser UI open marker: Start-Process http://127.0.0.1:8766
rem Legacy direct web command marker: app.py --web
rem Docker diagnostic marker: docker info
rem Docker startup marker: Docker Desktop.exe
rem NOVA_SKIP_STARTUP_TESTS
rem Continue anyway for debugging
call "%~dp0START_NOVA_HERE.bat"
