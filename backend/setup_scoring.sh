#!/bin/bash

# 🎯 Scoring System Setup Script (T021-T023)
# This script sets up the environment for the core scoring components

echo "🚀 Setting up Core Scoring System (T021-T023)"
echo "=============================================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE "[0-9]+\.[0-9]+")
echo "📋 Python version: $python_version"

if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.8+ required. Current version: $python_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv_scoring" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv venv_scoring
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv_scoring/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install core dependencies for scoring
echo "📦 Installing core scoring dependencies..."
pip install numpy pandas scipy

# Install machine learning dependencies
echo "🤖 Installing machine learning dependencies..."
pip install scikit-learn

# Try to install implicit (may fail if build tools are missing)
echo "🔧 Installing implicit library for ALS..."
pip install implicit || {
    echo "⚠️  Warning: implicit installation failed. Will use fallback mode."
    echo "   This is not critical - personalized scoring will work in fallback mode."
}

# Install database dependencies
echo "🗄️  Installing database dependencies..."
pip install sqlalchemy asyncpg psycopg2-binary

# Install web framework dependencies
echo "🌐 Installing web framework dependencies..."
pip install fastapi pydantic pydantic-settings

# Install other utilities
echo "🛠️  Installing utility dependencies..."
pip install python-dateutil python-dotenv structlog

# Install testing dependencies
echo "🧪 Installing testing dependencies..."
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Verify installations
echo ""
echo "🔍 Verifying installations..."
echo "=============================================="

# Check critical packages
packages=("numpy" "pandas" "scipy" "sqlalchemy" "fastapi" "pydantic")
for package in "${packages[@]}"; do
    python3 -c "import $package; print(f'✅ {package}: {package.__version__}')" 2>/dev/null || \
    echo "❌ $package: Failed to import"
done

# Check optional packages
echo ""
echo "Optional packages:"
python3 -c "import implicit; print(f'✅ implicit: {implicit.__version__}')" 2>/dev/null || \
echo "⚠️  implicit: Not available (fallback mode will be used)"

# Test basic scoring components
echo ""
echo "🧪 Testing scoring components..."
echo "=============================================="

# Create a simple test
cat > test_basic_import.py << 'EOF'
import sys
import traceback

def test_imports():
    """Test basic imports for scoring components"""
    try:
        print("Testing T021 basic imports...")
        import numpy as np
        import pandas as pd
        from datetime import datetime, timedelta
        print("✅ T021 dependencies OK")

        print("Testing T022 SEO imports...")
        import unicodedata
        print("✅ T022 dependencies OK")

        print("Testing T023 personalized imports...")
        try:
            import implicit
            print("✅ T023 dependencies OK (with implicit)")
        except ImportError:
            print("⚠️  T023 dependencies OK (fallback mode)")

        print("Testing database imports...")
        import sqlalchemy
        print("✅ Database dependencies OK")

        print("Testing web framework imports...")
        import fastapi
        import pydantic
        print("✅ Web framework dependencies OK")

        print("")
        print("🎉 All core dependencies are working!")
        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
EOF

# Run the test
python3 test_basic_import.py
test_result=$?

# Clean up test file
rm test_basic_import.py

# Summary
echo ""
echo "📊 Setup Summary"
echo "=============================================="

if [ $test_result -eq 0 ]; then
    echo "✅ Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Activate environment: source venv_scoring/bin/activate"
    echo "2. Run scoring tests: python3 test_scoring_integration.py"
    echo "3. Configure database: Update .env file with DATABASE_URL"
    echo "4. Initialize SEMRUSH data: Load keywords into database"
    echo ""
    echo "🚀 Ready to run T021-T023 scoring components!"
else
    echo "❌ Setup encountered issues. Please check the error messages above."
    echo ""
    echo "Common solutions:"
    echo "1. Install build tools: sudo apt-get install build-essential (Ubuntu/Debian)"
    echo "2. Install Python dev headers: sudo apt-get install python3-dev"
    echo "3. For macOS: Install Xcode command line tools"
    echo ""
fi

echo ""
echo "🔗 Useful commands:"
echo "• Activate environment: source venv_scoring/bin/activate"
echo "• Install additional packages: pip install package_name"
echo "• List installed packages: pip list"
echo "• Run tests: pytest tests/"
echo "• Check scoring integration: python3 test_scoring_integration.py"

deactivate