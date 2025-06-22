import os
import logging
import time
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from aws_services import aws_services
from models import mongodb

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set Flask and Werkzeug logging to WARNING to reduce noise
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

print("🚀 Starting AquaPulse: Smart Algae Bloom Detection and Prediction...")

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "plasticpulse-development-key-2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

print("📦 Initializing AWS services...")

# Import routes after app creation to avoid circular imports
from routes import *

print("🗄️  Initializing database...")

# Initialize sample data in MongoDB if needed
try:
    mongodb.initialize_sample_data()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️  Warning: Could not initialize sample data: {e}")

print("🔧 Setting up demo services...")

# Initialize demo services in background to avoid blocking startup
try:
    aws_services.recreate_demo_services()
    print("✅ Demo services setup completed")
except Exception as e:
    print(f"⚠️  Warning: Could not setup demo services: {e}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌊 AQUAPULSE: REAL-TIME INTELLIGENCE FOR A CLEANER PLANET")
    print("="*60)
    print("📊 Dashboard: http://localhost:5000")
    print("🔗 API Base: http://localhost:5000/api/")
    print("📚 Documentation: Check README.md for API endpoints")
    print("="*60)
    print("🚀 Starting Flask server...")
    print("⏳ Please wait a moment for the application to fully load...")
    print("="*60)
    
    # Start the Flask app
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=True,
        use_reloader=False  # Disable reloader to avoid duplicate processes
    )
