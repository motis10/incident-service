# Proxy Configuration

This document explains how to configure HTTP/HTTPS proxies for the Netanya Incident Service.

## Overview

The service supports proxy configuration through environment variables. This is useful when:
- The service runs behind a corporate firewall
- You need to route traffic through a specific proxy server
- You want to use a proxy for debugging (e.g., Charles Proxy, Fiddler)

## Configuration

### Environment Variables

Set one or both of these environment variables:

```bash
# HTTP proxy
PROXY_HTTP=http://proxy.example.com:8080

# HTTPS proxy  
PROXY_HTTPS=https://proxy.example.com:8443
```

### Docker Compose

Add the environment variables to your `docker-compose.yml`:

```yaml
services:
  incident-service:
    environment:
      - PROXY_HTTP=http://proxy.example.com:8080
      - PROXY_HTTPS=https://proxy.example.com:8443
```

### Cloud Run

Add the environment variables to your Cloud Run deployment:

```bash
gcloud run deploy incident-service \
  --set-env-vars="PROXY_HTTP=http://proxy.example.com:8080,PROXY_HTTPS=https://proxy.example.com:8443"
```

Or add them to your `deployment/production.yaml`:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
spec:
  template:
    spec:
      containers:
      - env:
        - name: PROXY_HTTP
          value: "http://proxy.example.com:8080"
        - name: PROXY_HTTPS
          value: "https://proxy.example.com:8443"
```

### GitHub Actions

Add the environment variables to your `.github/workflows/build-and-deploy.yml`:

```yaml
- name: Deploy to Cloud Run
  run: |
    gcloud run deploy ${{ env.SERVICE_NAME }} \
      --set-env-vars="PROXY_HTTP=http://proxy.example.com:8080,PROXY_HTTPS=https://proxy.example.com:8443"
```

## Proxy Format

The proxy URLs should follow this format:

```
http://[username:password@]host:port
https://[username:password@]host:port
```

Examples:

```bash
# Without authentication
PROXY_HTTP=http://proxy.example.com:8080

# With authentication
PROXY_HTTP=http://user:pass@proxy.example.com:8080

# Different proxies for HTTP and HTTPS
PROXY_HTTP=http://http-proxy.example.com:8080
PROXY_HTTPS=https://https-proxy.example.com:8443
```

## How It Works

1. The `ConfigService` reads the `PROXY_HTTP` and `PROXY_HTTPS` environment variables
2. The configuration is stored in the `AppConfig` dataclass
3. The `ProductionSharePointClient` retrieves the proxy config via `get_proxy_config()`
4. The proxy configuration is passed to the `SharePointClient` constructor
5. The `requests` library uses the proxy for all HTTP/HTTPS requests

## Debugging

To verify the proxy configuration is working:

1. Check the logs for proxy initialization:
   ```
   SharePointClient initialized with proxy configuration: {'http': 'http://...', 'https': 'https://...'}
   ```

2. If no proxy is configured:
   ```
   SharePointClient initialized without proxy configuration
   ```

## Disabling Proxy

To disable proxy usage, simply remove or unset the environment variables:

```bash
unset PROXY_HTTP
unset PROXY_HTTPS
```

Or remove them from your deployment configuration.

## Security Considerations

- **Never commit proxy credentials to version control**
- Use environment variables or secrets management for sensitive proxy credentials
- In Cloud Run, use Secret Manager for storing proxy credentials
- Ensure the proxy server is trusted and secure
- Use HTTPS proxies when possible to encrypt traffic between the service and proxy

## Troubleshooting

### Connection Refused

If you see "Connection refused" errors:
- Verify the proxy URL is correct
- Check that the proxy server is running and accessible
- Ensure firewall rules allow traffic to the proxy

### Authentication Failed

If you see "407 Proxy Authentication Required":
- Verify the username and password are correct
- Ensure credentials are properly URL-encoded
- Check if the proxy requires specific authentication headers

### SSL/TLS Errors

If you see SSL certificate errors:
- Verify the proxy supports HTTPS
- Check if the proxy uses a self-signed certificate
- You may need to add the proxy's CA certificate to the container

## Example: Using Charles Proxy for Debugging

To debug SharePoint API requests using Charles Proxy:

1. Start Charles Proxy on your local machine
2. Enable SSL proxying for `*.netanya.muni.il`
3. Note the proxy port (default: 8888)
4. Set environment variables:
   ```bash
   PROXY_HTTP=http://host.docker.internal:8888
   PROXY_HTTPS=http://host.docker.internal:8888
   ```
5. Start the service
6. All SharePoint requests will appear in Charles

Note: Use `host.docker.internal` to access the host machine from Docker.

