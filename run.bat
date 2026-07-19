@echo off
chcp 65001 >nul
title NASDAQ Stock Lookup Tool

echo Installing dependencies...
pip install -r requirements.txt

echo Starting NASDAQ Stock Lookup Tool...
python nasdaq_tool.py

pause
