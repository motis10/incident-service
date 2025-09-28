# 🔧 Google Cloud Build Fix Guide

## 🚨 **Problem Fixed**

**Error:** `error: linker 'cc' not found` during `pydantic-core` compilation  
**Root Cause:** Missing build tools in Docker base image  
**Status:** ✅ **FIXED**

## 📋 **Solution Applied**

### **1. Updated Dockerfile with Build Tools**

Added essential build dependencies for Rust/C compilation:
```dockerfile
# Install build dependencies for Rust/C compilation
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        make \
        pkg-config \
        libssl-dev \
        libffi-dev \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*
```

### **2. Created Multiple Dockerfile Options**

#### **Option A: `Dockerfile` (Multi-stage - Optimized)**
- ✅ Build stage with all compilation tools
- ✅ Runtime stage with minimal dependencies  
- ✅ Smaller final image size
- ⚠️ More complex build process

#### **Option B: `Dockerfile.simple` (Single-stage - Reliable)**
- ✅ All tools in one stage
- ✅ Simpler build process
- ✅ More reliable for Cloud Build
- ⚠️ Larger final image

### **3. Added Cloud Build Configuration**

Created `cloudbuild.yaml` with:
- ✅ High-CPU machine for faster Rust compilation
- ✅ Extended timeout (30 minutes)
- ✅ Proper logging and error handling

## 🚀 **How to Deploy**

### **Option 1: Use Simple Dockerfile (Recommended for Cloud Build)**

```bash
# Build locally to test
docker build -f Dockerfile.simple -t netanya-incident-service .

# Deploy to Google Cloud Build
gcloud builds submit --config cloudbuild.yaml .
```

### **Option 2: Use Multi-stage Dockerfile**

```bash
# Build locally to test
docker build --target production -t netanya-incident-service .

# Deploy to Cloud Build (modify cloudbuild.yaml to use 'Dockerfile')
# Change: '-f', 'Dockerfile.simple' to '-f', 'Dockerfile'
gcloud builds submit --config cloudbuild.yaml .
```

### **Option 3: Manual Cloud Build**

```bash
# Submit build manually
gcloud builds submit --tag gcr.io/[PROJECT-ID]/netanya-incident-service .
```

## 🎯 **Why This Fixes the Error**

### **Root Cause Analysis:**
1. **pydantic-core** is a Rust-based Python package
2. **Rust compilation** requires C/C++ build tools
3. **python:3.13-slim** base image lacks these tools
4. **Cloud Build failed** when trying to compile pydantic-core

### **Solution Details:**
- **build-essential**: Provides `gcc`, `g++`, `make`
- **pkg-config**: For library configuration
- **libssl-dev**: SSL/TLS library headers
- **libffi-dev**: Foreign Function Interface library

## 📊 **Testing the Fix**

### **Local Testing:**
```bash
# Test the simple Dockerfile
docker build -f Dockerfile.simple -t test-build .
docker run -p 8000:8000 -e ENVIRONMENT=production test-build

# Test the API
curl http://localhost:8000/health
```

### **Cloud Build Testing:**
```bash
# Submit test build
gcloud builds submit --config cloudbuild.yaml .

# Check build logs
gcloud builds log [BUILD-ID]
```

## 🔧 **Build Performance Optimizations**

### **Applied Optimizations:**
1. **High-CPU Machine**: `E2_HIGHCPU_8` for faster Rust compilation
2. **Extended Timeout**: 30 minutes for complex builds
3. **Disk Space**: 100GB for large dependency compilation
4. **Layer Caching**: Optimized layer order for Docker caching

### **Expected Build Time:**
- **First build**: 15-20 minutes (compiling Rust dependencies)
- **Subsequent builds**: 5-10 minutes (with caching)

## ✅ **Verification**

After successful build, your logs should show:
```
Building wheel for pydantic-core (pyproject.toml): finished with status 'done'
Successfully built pydantic-core
```

Instead of:
```
error: linker `cc` not found
Building wheel for pydantic-core (pyproject.toml): finished with status 'error'
```

## 🎉 **Next Steps**

1. **✅ Use the fixed Dockerfile** - Choose simple or multi-stage
2. **✅ Deploy with Cloud Build** - Use provided `cloudbuild.yaml`
3. **✅ Test the deployment** - Verify API endpoints work
4. **✅ Monitor performance** - Check response times and scaling

Your Netanya Incident Service will now build successfully in Google Cloud Build! 🚀
