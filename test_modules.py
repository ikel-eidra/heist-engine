#!/usr/bin/env python3
"""
Quick test script to validate all modules load correctly
"""

import sys
import asyncio

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        from modules.the_ear import TheEar
        print("✅ The Ear imported successfully")
    except Exception as e:
        print(f"❌ The Ear import failed: {e}")
        return False
    
    try:
        from modules.the_eye import TheEye
        print("✅ The Eye imported successfully")
    except Exception as e:
        print(f"❌ The Eye import failed: {e}")
        return False
    
    try:
        from modules.the_hand import TheHand
        print("✅ The Hand imported successfully")
    except Exception as e:
        print(f"❌ The Hand import failed: {e}")
        return False
    
    return True

async def test_initialization():
    """Test that modules can be initialized"""
    print("\nTesting module initialization...")
    
    from modules.the_ear import TheEar
    from modules.the_eye import TheEye
    from modules.the_hand import TheHand
    
    try:
        ear = TheEar()
        print("✅ The Ear instantiated")
    except Exception as e:
        print(f"❌ The Ear instantiation failed: {e}")
        return False
    
    try:
        eye = TheEye()
        await eye.initialize()
        print("✅ The Eye initialized")
        await eye.shutdown()
    except Exception as e:
        print(f"❌ The Eye initialization failed: {e}")
        return False
    
    try:
        hand = TheHand()
        await hand.initialize()
        print("✅ The Hand initialized")
        await hand.stop()
    except Exception as e:
        print(f"❌ The Hand initialization failed: {e}")
        return False
    
    return True

async def main():
    print("="*60)
    print("HEIST ENGINE - MODULE VALIDATION TEST")
    print("="*60)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed")
        sys.exit(1)
    
    # Test initialization
    if not await test_initialization():
        print("\n❌ Initialization test failed")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    print("\nThe Heist Engine is ready for deployment.")

if __name__ == '__main__':
    asyncio.run(main())
