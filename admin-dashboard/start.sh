#!/bin/bash
# AX Admin Dashboard 시작 스크립트

echo "🚀 Starting AX Admin Dashboard..."

# Install dependencies
pip3 install -r requirements.txt --user

# Start dashboard
python3 dashboard.py
