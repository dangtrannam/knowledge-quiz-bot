#!/usr/bin/env python3
"""
Startup script for Knowledge Quiz Bot
Checks dependencies and launches the Streamlit application
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'openai', 
        'langchain',
        'chromadb',
        'PyPDF2',
        'docx'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
        else:
            print(f"✅ {package} is installed")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    return True

def check_api_key():
    """Check if OpenAI API key is set"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️  OpenAI API key not found")
        print("   You can still run the app and enter the key in the sidebar")
        print("   Or set it as environment variable: export OPENAI_API_KEY='your-key'")
        return False
    
    if api_key.startswith('sk-'):
        print("✅ OpenAI API key is set")
        return True
    else:
        print("⚠️  API key format looks incorrect (should start with 'sk-')")
        return False

def launch_streamlit():
    """Launch the Streamlit application"""
    try:
        print("\n🚀 Launching Knowledge Quiz Bot...")
        print("   The app will open in your browser automatically")
        print("   Press Ctrl+C to stop the server")
        
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error launching app: {str(e)}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🧠 Knowledge Quiz Bot - Startup Check")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        return 1
    
    print("\n🔑 Checking API key...")
    check_api_key()  # Don't fail if API key is missing
    
    print("\n" + "=" * 50)
    print("✅ All checks passed! Ready to start the quiz bot.")
    
    # Ask user if they want to launch
    try:
        response = input("\nWould you like to launch the app now? (y/n): ").lower().strip()
        if response in ['y', 'yes', '']:
            launch_streamlit()
        else:
            print("\n👍 To start the app later, run: streamlit run app.py")
            
    except KeyboardInterrupt:
        print("\n👋 See you later!")
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 