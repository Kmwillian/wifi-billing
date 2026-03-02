#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🎨 Collecting static files..."
python manage.py collectstatic --no-input

echo "🗄️ Running migrations..."
python manage.py migrate

echo "🌱 Populating sample data..."
python manage.py populate_test_data

echo "✅ Build complete!"