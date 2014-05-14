rem This ensures that we use the Virtualenv's python.exe on Windows platforms!
set PROJECT_DIR=%~dp0
set LIB_DIR=%PROJECT_DIR%bitsofeight\lib
set PATH=%PATH%;%LIB_DIR%
python.exe run_game.py