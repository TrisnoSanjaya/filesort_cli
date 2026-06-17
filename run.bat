@echo off
setlocal enabledelayedexpansion

REM Prompt sederhana untuk File Sorter
set /p "src=Masukkan folder sumber: "
if "%src%"=="" (
  echo Folder sumber tidak boleh kosong.
  pause
  exit /b 1
)

set /p "dst=Masukkan folder tujuan (kosongkan untuk default=di dalam folder sumber): "

set /p "mode=Pilih mode (move/copy) [move]: "
if /i "!mode!"=="copy" (
  set mode_arg=--mode copy
) else (
  set mode_arg=--mode move
)

set /p "rec=Rekursif? (y/n) [n]: "
if /i "!rec!"=="y" (
  set rec_arg=--recursive
) else (
  set rec_arg=
)

set /p "incfold=Sertakan folder juga? (y/n) [n]: "
if /i "!incfold!"=="y" (
  set fold_arg=--include-folders
) else (
  set fold_arg=
)

set /p "dry=Dry-run? (y/n) [n]: "
if /i "!dry!"=="y" (
  set dry_arg=--dry-run
) else (
  set dry_arg=
)

set "cmdline=python file_sorter.py --source "%src%" !mode_arg! !rec_arg! !fold_arg! !dry_arg!"

if not "%dst%"=="" (
  set "cmdline=!cmdline! --destination "%dst%""
)

echo.
echo Menjalankan: !cmdline!
echo.

!cmdline!

echo.
pause
