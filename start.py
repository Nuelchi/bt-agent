#!/usr/bin/env python3
"""
Trading Agent Backtester Startup Script
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'langchain', 'openai', 
        'pandas', 'numpy', 'backtesting', 'yfinance'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall them with: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_env_file():
    """Check if environment file exists and has API key"""
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("   Copy env_example.txt to .env and add your OpenAI API key")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
        if 'your_openai_api_key_here' in content or 'OPENAI_API_KEY=' not in content:
            print("⚠️  OpenAI API key not configured in .env file")
            print("   Please add your actual API key to the .env file")
            return False
    
    print("✅ Environment configuration found")
    return True

def create_data_cache():
    """Create data cache directory if it doesn't exist"""
    cache_dir = Path('data_cache')
    cache_dir.mkdir(exist_ok=True)
    print("✅ Data cache directory ready")

def main():
    """Main startup function"""
    print("🚀 Trading Agent Backtester")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        print("\n💡 To continue without API key (limited functionality):")
        print("   export OPENAI_API_KEY=your_key_here")
        print("   python main.py")
        sys.exit(1)
    
    # Create cache directory
    create_data_cache()
    
    print("\n🎯 Starting server...")
    print("   Open http://localhost:8000 in your browser")
    print("   Press Ctrl+C to stop")
    print("=" * 40)
    
    # Start the server
    try:
        subprocess.run([sys.executable, 'main.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 