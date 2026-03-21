# Backend Scripts

Testing and verification scripts for the GeoChallenge backend.

## 📜 Available Scripts

### Import Verification

**[verify_imports.py](./verify_imports.py)**
```bash
python3 scripts/verify_imports.py
```

**Purpose:** Comprehensive verification that all backend imports work correctly

**What it does:**
- Tests direct service imports
- Tests package imports
- Tests API route imports
- Verifies all endpoints are registered
- Shows diagnostic information for IDE troubleshooting

**When to use:**
- After modifying import statements
- When IDE shows false positive import errors
- To verify project setup after cloning
- Before deployment

### API Testing

**[test_boundaries.py](./test_boundaries.py)**
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run tests
python scripts/test_boundaries.py
```

**Purpose:** Comprehensive test suite for the boundaries API

**What it does:**
- Tests all boundary API endpoints
- Verifies request/response models
- Tests error handling (404, validation)
- Uses mocked database for fast testing
- Reports pass/fail for each test

**Test Coverage:**
- ✅ Import validation
- ✅ POST `/api/boundaries/check-point`
- ✅ GET `/api/boundaries/country/{name}`
- ✅ 404 error handling
- ✅ POST `/api/boundaries/countries`

**When to use:**
- After modifying boundaries API code
- Before committing changes
- To verify API functionality
- During development

## 🚀 Quick Commands

### Verify Everything Works
```bash
cd geochallenge-backend

# Test imports
python3 scripts/verify_imports.py

# Test API (requires httpx)
source .venv/bin/activate
pip install httpx  # if not already installed
python scripts/test_boundaries.py
```

### Run All Checks
```bash
cd geochallenge-backend

# 1. Check imports
echo "Checking imports..."
python3 scripts/verify_imports.py

# 2. Test boundaries API
echo "Testing boundaries API..."
source .venv/bin/activate
python scripts/test_boundaries.py

# 3. Test database connection (if configured)
echo "Testing database..."
python3 ../scripts/test_remote_connection.py
```

## 📋 Requirements

### Python Version
- Python 3.12 or higher

### Dependencies
```bash
pip install -r requirements.txt
```

### For test_boundaries.py
```bash
pip install httpx  # Required for FastAPI TestClient
```

## 🔍 Interpreting Results

### verify_imports.py

**Success Output:**
```
✅ services.boundary_service imports successfully
✅ api.routes.boundaries imports successfully
✅ Router has 3 endpoints
✅ ALL IMPORTS WORK CORRECTLY!
```

**Failure Output:**
```
❌ Failed: No module named 'services'
```
→ Check Python path and module structure

### test_boundaries.py

**Success Output:**
```
Passed: 5/5
🎉 All tests passed!
```

**Failure Output:**
```
Passed: 3/5
⚠️  2 test(s) failed
```
→ Check error details in output above

## 🐛 Troubleshooting

### "No module named 'services'" Error

**Solution:**
```bash
# Ensure you're in the backend directory
cd geochallenge-backend

# Run script
python3 scripts/verify_imports.py
```

### "No module named 'httpx'" Error

**Solution:**
```bash
source .venv/bin/activate
pip install httpx
```

### IDE Shows Import Errors

**Solution:**
1. Run `python3 scripts/verify_imports.py`
2. If tests pass, read [../docs/IDE_IMPORT_FIX.md](../docs/IDE_IMPORT_FIX.md)
3. Restart your IDE

### Tests Fail

**Check:**
1. Dependencies installed: `pip install -r requirements.txt`
2. Correct Python version: `python3 --version` (should be 3.12+)
3. In correct directory: `pwd` (should end in `/geochallenge-backend`)
4. Virtual environment activated: `which python3`

## 💡 Adding New Scripts

When adding new test scripts:

1. **Name convention:** `test_*.py` or `verify_*.py`
2. **Add shebang:** `#!/usr/bin/env python3`
3. **Make executable:** `chmod +x scripts/your_script.py`
4. **Document:** Add to this README
5. **Exit codes:** Use `sys.exit(0)` for success, `sys.exit(1)` for failure

## 📖 Related Documentation

- [Backend Documentation](../docs/README.md) - IDE import fixes and guides
- [Root Scripts](../../scripts/README.md) - Database setup scripts
- [Main Backend README](../README.md) - Backend structure and setup

## 🆘 Need Help?

- **Import errors:** Run `python3 scripts/verify_imports.py` and see [../docs/IDE_IMPORT_FIX.md](../docs/IDE_IMPORT_FIX.md)
- **Test failures:** Check error messages in test output
- **Setup issues:** See [../README.md](../README.md)
