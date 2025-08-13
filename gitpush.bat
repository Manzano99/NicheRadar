@echo off
setlocal EnableExtensions

REM === Comprobaciones básicas ===
where git >nul 2>nul || (echo [ERROR] Git no esta en PATH. & goto :end)
git rev-parse --is-inside-work-tree >nul 2>nul || (echo [ERROR] No estas dentro de un repositorio Git. & goto :end)

REM === Info rapida ===
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set "BRANCH=%%b"
echo Rama actual: %BRANCH%
git status -sb
echo.

REM === Staging ===
git add -A

REM === ¿Hay algo staged? si no, saltar a push ===
git diff --cached --quiet
if errorlevel 1 goto do_commit

echo No hay cambios para commitear. (Se hara solo push)
goto do_push

:do_commit
REM Leer mensaje SIN delayed expansion (para permitir ! en el texto)
setlocal DisableDelayedExpansion
set "msg="
set /p msg=Mensaje para commit: 
if "%msg%"=="" set "msg=update"
endlocal & set "msg=%msg%"

echo Commit: "%msg%"
git commit -m "%msg%"

:do_push
REM === Push (crea upstream automaticamente si no existe) ===
git rev-parse --abbrev-ref --symbolic-full-name @{u} >nul 2>nul
if errorlevel 1 (
    echo No hay upstream configurado. Creando upstream origin/%BRANCH%...
    git push --set-upstream origin %BRANCH%
) else (
    git push
)

if errorlevel 1 (
    echo [ERROR] Fallo el push.
) else (
    echo ✓ Push correcto a %BRANCH%.
)

:end
echo.
pause
exit /b 0