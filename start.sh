#!/bin/bash

# ERISA Recovery Dashboard - Quick Start Script

echo "🏥 ERISA Assessment Claims Dashboard"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# We're already in the right directory
echo "📁 Working in: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️  Setting up database..."
python manage.py migrate

# Check if superuser exists, if not create one
echo "👤 Setting up admin user..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Created admin user: admin/admin123')
else:
    print('Admin user already exists: admin/admin123')
"

# Load sample data if claims table is empty
echo "📊 Loading sample data..."
python manage.py shell -c "
from apps.claims.models import Claim
if Claim.objects.count() == 0:
    print('Loading sample claims data...')
    import subprocess
    subprocess.run(['python', 'manage.py', 'load_claims_data', '--claims-file', 'claim_list_data.csv', '--details-file', 'claim_detail_data.csv'])
else:
    print('Sample data already loaded ({} claims)'.format(Claim.objects.count()))
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting development server..."
echo "📱 Access the application at: http://127.0.0.1:8000/"
echo "🔑 Login with: admin / admin123"
echo "⚙️  Admin interface: http://127.0.0.1:8000/admin/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
python manage.py runserver