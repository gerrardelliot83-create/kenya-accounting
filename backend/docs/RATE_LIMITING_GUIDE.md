# Rate Limiting Quick Reference Guide

## For Backend Developers

### Adding Rate Limits to New Endpoints

#### 1. Import Required Modules
```python
from fastapi import Request  # Required for rate limiting
from app.core.rate_limiter import limiter, RATE_LIMITS
```

#### 2. Add Request Parameter
```python
# Before
async def my_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):

# After
async def my_endpoint(
    request: Request,  # Add this
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
```

#### 3. Add Rate Limit Decorator
```python
@router.post("/my-endpoint")
@limiter.limit(RATE_LIMITS["create"])  # Add this decorator
async def my_endpoint(request: Request, ...):
    pass
```

### Choosing the Right Rate Limit

| Operation Type | Rate Limit | Use Case |
|---------------|-----------|----------|
| `auth_login` | 5/minute | Login attempts |
| `auth_password` | 3/minute | Password changes |
| `auth_refresh` | 10/minute | Token refresh |
| `create` | 30/minute | Creating resources |
| `update` | 50/minute | Updating resources |
| `delete` | 20/minute | Deleting resources |
| `read` | 100/minute | Reading/listing |
| `read_heavy` | 50/minute | Heavy reports |
| `export_pdf` | 10/minute | PDF generation |
| `export_csv` | 15/minute | CSV export |
| `upload` | 5/minute | File uploads |
| `import` | 5/minute | Data imports |
| `reconcile` | 20/minute | Bank reconciliation |
| `reports` | 30/minute | Financial reports |

### Complete Example

```python
from fastapi import APIRouter, Depends, Request
from app.core.rate_limiter import limiter, RATE_LIMITS

router = APIRouter()

# Read operation - lenient limit
@router.get("/items")
@limiter.limit(RATE_LIMITS["read"])
async def list_items(request: Request, ...):
    pass

# Create operation - moderate limit
@router.post("/items")
@limiter.limit(RATE_LIMITS["create"])
async def create_item(request: Request, ...):
    pass

# PDF export - strict limit
@router.get("/items/{id}/pdf")
@limiter.limit(RATE_LIMITS["export_pdf"])
async def export_pdf(request: Request, ...):
    pass

# Custom rate limit
@router.post("/bulk-import")
@limiter.limit("10/hour")  # Custom: 10 per hour
async def bulk_import(request: Request, ...):
    pass
```

### Testing Your Rate Limits

```bash
# Test with curl (repeat quickly)
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/your-endpoint \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"data":"test"}' \
    -w "\nStatus: %{http_code}\n"
  sleep 0.5
done
```

### Common Pitfalls

❌ **Forgot to add Request parameter**
```python
@limiter.limit(RATE_LIMITS["create"])
async def create_item(data: ItemCreate, ...):  # Missing request: Request
    pass
# Result: TypeError
```

✅ **Correct**
```python
@limiter.limit(RATE_LIMITS["create"])
async def create_item(request: Request, data: ItemCreate, ...):
    pass
```

❌ **Rate limit decorator in wrong position**
```python
@limiter.limit(RATE_LIMITS["create"])
@router.post("/items")  # Decorator order matters!
async def create_item(...):
    pass
# Result: May not work correctly
```

✅ **Correct**
```python
@router.post("/items")
@limiter.limit(RATE_LIMITS["create"])  # After router decorator
async def create_item(...):
    pass
```

### Custom Rate Limits

When predefined limits don't fit your use case:

```python
# Per minute
@limiter.limit("50/minute")

# Per hour
@limiter.limit("1000/hour")

# Per day
@limiter.limit("10000/day")

# Multiple limits (most restrictive applies)
@limiter.limit("5/second;50/minute;500/hour")
```

### Response to Rate Limit Exceeded

When a user exceeds the rate limit, they receive:

**Status Code:** 429 Too Many Requests

**Response Body:**
```json
{
  "error": "RateLimitExceeded",
  "message": "Too many requests. Please try again later.",
  "detail": "You have exceeded the rate limit for this endpoint.",
  "path": "/api/v1/items",
  "retry_after_seconds": 60
}
```

**Headers:**
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1234567890
Retry-After: 60
```

### Debugging Rate Limits

**Check logs for violations:**
```bash
grep "Rate limit exceeded" logs/app.log
```

**Example log entry:**
```
WARNING - Rate limit exceeded: 192.168.1.100 - POST /api/v1/items - 1 per 1 minute
```

### Production Considerations

**Current Setup (Memory Storage):**
- ✅ Fast, no dependencies
- ❌ Lost on restart
- ❌ Not shared across multiple server instances
- **Best for:** Development, single-instance staging

**Production Setup (Redis Storage):**
- ✅ Persistent across restarts
- ✅ Shared across multiple server instances
- ✅ Distributed rate limiting
- **Required for:** Production with multiple instances

**Migration to Redis:**
```python
# In app/core/rate_limiter.py
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["100/minute"],
    storage_uri="redis://localhost:6379",  # Change from "memory://"
)
```

### Advanced: Per-User Rate Limiting

By default, rate limits are per-IP. For authenticated endpoints, you can rate limit per user:

```python
# In app/core/rate_limiter.py
def get_identifier(request: Request) -> str:
    # Check if user is authenticated
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    # Fall back to IP for unauthenticated requests
    return get_remote_address(request)
```

This allows:
- Different users from same IP (office, shared network) get separate limits
- More accurate tracking of abuse
- Better handling of legitimate power users

### Questions?

For issues or questions about rate limiting:
1. Check the logs for rate limit violations
2. Review `SECURITY_HARDENING_SUMMARY.md` for detailed documentation
3. Consult the team's senior backend developer
4. See SlowAPI documentation: https://github.com/laurentS/slowapi

---

**Quick Checklist for New Endpoints:**
- [ ] Imported `Request` from `fastapi`
- [ ] Imported `limiter` and `RATE_LIMITS` from `app.core.rate_limiter`
- [ ] Added `request: Request` parameter to function signature
- [ ] Added `@limiter.limit(RATE_LIMITS["..."])` decorator
- [ ] Chose appropriate rate limit type
- [ ] Tested rate limit works (make multiple rapid requests)
- [ ] Updated API documentation with rate limit info
