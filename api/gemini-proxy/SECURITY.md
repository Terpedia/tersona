# Security Configuration

## Origin Validation

The Cloud Function only accepts requests from allowed origins:

- `https://tersona.terpedia.com` (production)
- `https://terpedia.github.io` (GitHub Pages fallback)
- `http://localhost:3000` (local development)
- `http://localhost:5173` (local development)

## How It Works

1. **Origin Check**: The function validates the `Origin` or `Referer` header
2. **CORS**: Only allowed origins receive CORS headers
3. **Rejection**: Requests from other origins receive `403 Forbidden`

## Deployment Options

### Option 1: Origin Validation (Current)
- Function validates origin in code
- Allows requests from any IP, but checks origin header
- Good for public-facing services

### Option 2: Ingress Restriction
- Use `--ingress-settings internal-and-gclb` to restrict to Google Cloud Load Balancer
- Requires setting up a Load Balancer in front
- More secure but more complex

### Option 3: API Key Authentication
Add API key validation:
```python
API_KEY = os.getenv("CHAT_API_KEY")

def validate_api_key(request):
    api_key = request.headers.get("X-API-Key")
    return api_key == API_KEY
```

## Testing

Test from allowed origin:
```bash
curl -X POST https://your-function-url/chat \
  -H "Origin: https://tersona.terpedia.com" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

Test from blocked origin (should fail):
```bash
curl -X POST https://your-function-url/chat \
  -H "Origin: https://evil.com" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
# Should return 403 Forbidden
```
