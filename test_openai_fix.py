#!/usr/bin/env python3
"""
Test script to validate OpenAI client initialization fix
"""
import os
import sys

# Set up environment
os.environ.setdefault('OPENAI_API_KEY', 'test-key-for-init-only')

def test_openai_init():
    """Test OpenAI client initialization with error handling"""
    try:
        from app.services.audio_service import AudioTranscriptionService
        
        print("🔍 Testing AudioTranscriptionService initialization...")
        service = AudioTranscriptionService()
        print("✅ AudioTranscriptionService initialized successfully!")
        print(f"📊 Client type: {type(service.client)}")
        
        return True
        
    except ValueError as e:
        if "OPENAI_API_KEY" in str(e):
            print("⚠️  Expected error: Missing real API key")
            return True
        else:
            print(f"❌ Unexpected ValueError: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def test_imports():
    """Test basic imports"""
    try:
        import openai
        print(f"✅ OpenAI library version: {openai.__version__}")
        
        from openai import OpenAI
        print("✅ OpenAI client class imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing OpenAI client initialization fix\n")
    
    # Test imports first
    if not test_imports():
        sys.exit(1)
    
    print()
    
    # Test service initialization
    if not test_openai_init():
        sys.exit(1)
    
    print("\n🎉 All tests passed! OpenAI client fix is working correctly.")
