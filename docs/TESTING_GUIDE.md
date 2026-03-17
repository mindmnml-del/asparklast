# AISpark Studio - Testing Guide

## Test Suite Overview

### Test Structure
```
backend/tests/
├── __init__.py
├── conftest.py                 # Pytest configuration
├── test_vertex_search.py       # Vertex AI Search tests
├── test_api_endpoints.py       # API endpoint tests
├── unit/                       # Unit tests
│   └── __init__.py
└── integration/                # Integration tests
    └── __init__.py
```

### Running Tests

#### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx
```

#### Run All Tests
```bash
# From backend directory
cd backend
python -m pytest tests/ -v
```

#### Run Specific Test Files
```bash
# Test Vertex AI Search functionality
python -m pytest tests/test_vertex_search.py -v

# Test API endpoints
python -m pytest tests/test_api_endpoints.py -v
```

#### Run with Coverage
```bash
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

## Test Categories

### 1. Vertex AI Search Tests (`test_vertex_search.py`)
**Purpose:** Ensure existing RAG system remains functional

- ✅ Service availability check
- ✅ Configuration validation  
- ✅ Search functionality testing
- ✅ Knowledge base document access (34 documents)
- ✅ Error handling verification

**Critical Tests:**
```python
def test_service_availability():
    # Ensures Vertex Search is working
    
async def test_search_functionality():
    # Tests actual search with sample queries
    
async def test_knowledge_base_documents():
    # Verifies 34 documents are accessible
```

### 2. API Endpoint Tests (`test_api_endpoints.py`)
**Purpose:** Validate all API endpoints work correctly

- ✅ Health check endpoints
- ✅ Authentication requirements
- ✅ Vertex Search status endpoint
- ✅ Critic analysis endpoints
- ✅ Token-based authentication flow

**Test Coverage:**
- Unauthorized access (401 errors)
- Endpoint existence (not 404)
- Authenticated access with valid tokens
- Response structure validation

### 3. Configuration Tests (`conftest.py`)
**Purpose:** Test environment setup and fixtures

- ✅ Async event loop configuration
- ✅ Test data fixtures
- ✅ Sample prompt data
- ✅ Test session management

## Expected Test Results

### Passing Tests Indicate:
- ✅ Vertex AI Search is working with 34 documents
- ✅ RAG system is functional
- ✅ API authentication is working
- ✅ All critical endpoints are accessible
- ✅ Database connections are stable

### If Tests Fail:
1. **Vertex Search Issues:**
   - Check service account key file exists
   - Verify DataStore ID configuration
   - Confirm Google Cloud permissions

2. **API Issues:**
   - Ensure backend is running on port 8001
   - Check database initialization
   - Verify JWT token generation

3. **Authentication Issues:**
   - Check user creation in database
   - Verify password hashing
   - Confirm token validation

## Test Data

### Sample Queries for RAG Testing:
- "photography lighting techniques"
- "video production workflow"  
- "camera settings for portraits"
- "creative composition rules"

### Test User Credentials:
```python
{
    "username": "pytest_user",
    "email": "pytest@example.com", 
    "password": "pytest_password_123"
}
```

## Continuous Testing

### Pre-Implementation Testing:
**Run before making any changes:**
```bash
python -m pytest tests/ -v --tb=short
```

### Post-Implementation Testing:
**Run after adding new features:**
```bash
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

### Integration Testing:
**Test with running application:**
```bash
# Start backend first
cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8001 &

# Run tests
python -m pytest tests/test_api_endpoints.py -v
```

## Next Steps

1. **Run Initial Tests:**
   ```bash
   cd backend && python -m pytest tests/ -v
   ```

2. **Fix Any Failing Tests Before Implementation**

3. **Add Character Lock Tests:**
   - Create `tests/unit/test_character_lock.py`
   - Test CharacterSheet validation
   - Test CharacterLockManager functionality

4. **Add Helios Prompt Tests:**
   - Create `tests/unit/test_helios_prompts.py`
   - Test personality selection
   - Test prompt composition

## Success Criteria

✅ All existing functionality tests pass  
✅ Vertex AI Search works with 34 documents  
✅ RAG system returns relevant results  
✅ API authentication flow works  
✅ No breaking changes to existing features