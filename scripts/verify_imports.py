#!/usr/bin/env python3
"""
Diagnostic script to verify all imports work correctly.
Run this to confirm boundaries.py imports are functional.
"""

import sys
from pathlib import Path

# Ensure we're in the backend directory
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("IMPORT VERIFICATION DIAGNOSTIC")
print("="*60)

# Test 1: Direct import of boundary_service
print("\n1. Testing direct boundary_service import...")
try:
    from services.boundary_service import BoundaryService, get_boundary_service
    print("   ✅ services.boundary_service imports successfully")
    service = get_boundary_service()
    print(f"   ✅ get_boundary_service() returns: {type(service).__name__}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# Test 2: Import via services package
print("\n2. Testing import via services package...")
try:
    from services import get_boundary_service as gbs
    print("   ✅ services package exports get_boundary_service")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# Test 3: Import boundaries.py route
print("\n3. Testing boundaries.py route imports...")
try:
    from api.routes.boundaries import (
        router,
        PointCheckRequest,
        PointCheckResponse,
        BoundaryResponse,
        MultipleBoundariesRequest
    )
    print("   ✅ api.routes.boundaries imports successfully")
    print(f"   ✅ Router has {len(router.routes)} endpoints:")
    for route in router.routes:
        methods = ', '.join(route.methods)
        print(f"      • {methods:6} {route.path}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Import main app
print("\n4. Testing main app imports...")
try:
    from api.main import app
    print("   ✅ api.main imports successfully")
    print(f"   ✅ App has {len(app.routes)} total routes")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# Test 5: Verify all route files
print("\n5. Testing all route files...")
try:
    from api.routes import game, scores, challenges, boundaries
    print("   ✅ All route modules import successfully")
    print(f"      • game: {len(game.router.routes)} endpoints")
    print(f"      • scores: {len(scores.router.routes)} endpoints")
    print(f"      • challenges: {len(challenges.router.routes)} endpoints")
    print(f"      • boundaries: {len(boundaries.router.routes)} endpoints")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL IMPORTS WORK CORRECTLY!")
print("="*60)
print("\nIf your IDE still shows errors, try:")
print("  1. Restart your IDE/language server")
print("  2. Reload the window (VS Code: Cmd/Ctrl+Shift+P → Reload Window)")
print("  3. Clear Python cache: rm -rf **/__pycache__")
print("  4. Check IDE is using correct Python interpreter:")
print("     ", sys.executable)
print("\nThe code is functional - IDE errors are false positives.")