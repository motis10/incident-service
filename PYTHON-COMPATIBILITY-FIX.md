# Python 3.13 Compatibility Fix for Cloud Run

## Problem

When deploying to Google Cloud Run with GitHub integration, the build failed due to:

1. **Outdated Pydantic Version**: 
   ```
   TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
   ```
   This occurred because `pydantic==2.4.2` and `pydantic-core==2.10.1` are not compatible with Python 3.13.

2. **Missing Build Tools**:
   ```
   error: linker 'cc' not found
   ```
   Required for compiling Rust-based dependencies like `pydantic-core`.

## Solution

### 1. Keep Python 3.13 with Updated Dependencies
- **Kept**: `python:3.13-slim` 
- **Updated**: Dependencies to Python 3.13 compatible versions
- **Reason**: Python 3.13 is the latest and works great with updated packages

### 2. Updated Dependencies
Updated `requirements.txt` and `requirements.cloud.txt` with Python 3.13 compatible versions:

```txt
# Core FastAPI Dependencies - Python 3.13 compatible versions
fastapi==0.116.1
pydantic==2.11.9        # ← Updated from 2.4.2
uvicorn[standard]==0.35.0

# HTTP client for SharePoint integration  
requests==2.32.5

# Testing dependencies
pytest==8.4.2
pytest-asyncio==0.21.1
httpx==0.28.1

# Development dependencies
black==24.10.0
flake8==7.1.1
python-dotenv==1.0.1

# File handling and validation
python-magic==0.4.27
Pillow>=11.0.0

# Production server
gunicorn==23.0.0

# Configuration management
PyYAML==6.0.1
```

### 3. Enhanced All Dockerfiles
- `Dockerfile`: Multi-stage build with Python 3.13 + build tools
- `Dockerfile.simple`: Single-stage build with Python 3.13 + build tools
- `Dockerfile.cloud`: Cloud-optimized build with Python 3.13 + build tools

## Key Changes

| Component | Before | After | Reason |
|-----------|--------|-------|---------|
| Python Base Image | `python:3.13-slim` | `python:3.13-slim` | Keep latest Python version |
| Pydantic | `2.4.2` | `2.11.9` | Python 3.13 compatibility + latest features |
| FastAPI | `0.104.1` | `0.116.1` | Latest stable version |
| Uvicorn | `0.24.0` | `0.35.0` | Performance improvements |
| Requests | `2.31.0` | `2.32.5` | Security updates |
| HTTPx | `0.25.2` | `0.28.1` | Bug fixes |
| Pytest | `7.4.3` | `8.4.2` | Latest testing features |

## Deployment for GitHub + Cloud Run

Since you're using **GitHub integration with Google Cloud Run** (not Cloud Build), no additional configuration files are needed. Google Cloud Run will:

1. Detect the `Dockerfile` in your repository
2. Build the image using the updated Python 3.12 base
3. Install dependencies using the updated `requirements.txt`
4. Deploy the service automatically

## Verification

After deployment, verify the fix by checking:

1. **Service Health**: `GET /health`
2. **Service Info**: Check logs for Python version
3. **API Functionality**: `POST /incidents/submit`

## Why This Fix Works

- **Python 3.13**: Latest Python version with all modern features
- **Pydantic 2.11.9**: Latest version with full Python 3.13 support and bug fixes  
- **Build Tools**: Included in all Dockerfiles for Rust compilation (`build-essential`, `gcc`, `g++`, etc.)
- **Updated Dependencies**: All packages updated to their latest stable versions compatible with Python 3.13

This ensures your **Netanya Incident Service** deploys successfully to Google Cloud Run! 🚀
