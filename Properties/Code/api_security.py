"""
API Security Layer for Polylog6
================================

Provides:
- Rate limiting (token bucket algorithm)
- API key authentication
- CORS configuration
- Request validation
- Security headers
- Audit logging
"""

import time
import hashlib
import hmac
import secrets
from typing import Optional, Dict, Callable, Any, Set
from collections import defaultdict
from dataclasses import dataclass
from functools import wraps
from datetime import datetime, timedelta
import threading
import json

from fastapi import HTTPException, Header, Request
from fastapi.responses import JSONResponse


@dataclass
class APIKey:
    """Represents an API key with metadata"""
    key_id: str
    secret_hash: str  # SHA256 hash of secret
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    enabled: bool = True
    rate_limit_rpm: int = 1000  # Requests per minute
    allowed_endpoints: Optional[Set[str]] = None  # None = all endpoints


class RateLimiter:
    """Token bucket rate limiter (thread-safe)"""
    
    def __init__(self, default_rpm: int = 1000, cleanup_interval: float = 60.0):
        self.default_rpm = default_rpm
        self.cleanup_interval = cleanup_interval
        self._buckets: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "tokens": self.default_rpm,
            "last_refill": time.time(),
            "requests": 0,
            "blocked_until": None
        })
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
    
    def is_allowed(self, client_id: str, max_tokens: int = None) -> bool:
        """Check if request is allowed for client"""
        if max_tokens is None:
            max_tokens = self.default_rpm
        
        with self._lock:
            bucket = self._buckets[client_id]
            now = time.time()
            
            # Check if client is blocked
            if bucket.get("blocked_until") and now < bucket["blocked_until"]:
                return False
            
            # Refill tokens (max tokens per minute)
            elapsed = now - bucket["last_refill"]
            refill_rate = max_tokens / 60.0  # tokens per second
            bucket["tokens"] = min(
                max_tokens,
                bucket["tokens"] + (elapsed * refill_rate)
            )
            bucket["last_refill"] = now
            
            # Check if token available
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                bucket["requests"] += 1
                
                # Periodic cleanup
                if now - self._last_cleanup > self.cleanup_interval:
                    self._cleanup_old_buckets()
                    self._last_cleanup = now
                
                return True
            
            # Rate limit exceeded - block for 1 minute
            bucket["blocked_until"] = now + 60
            return False
    
    def _cleanup_old_buckets(self):
        """Remove buckets inactive for 24 hours"""
        now = time.time()
        cutoff = now - 86400
        to_remove = [
            cid for cid, bucket in self._buckets.items()
            if bucket["last_refill"] < cutoff
        ]
        for cid in to_remove:
            del self._buckets[cid]
    
    def get_stats(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit stats for client"""
        with self._lock:
            bucket = self._buckets.get(client_id, {})
            return {
                "tokens_remaining": int(bucket.get("tokens", 0)),
                "total_requests": bucket.get("requests", 0),
                "blocked_until": bucket.get("blocked_until"),
            }


class APIKeyManager:
    """Manages API keys and validation"""
    
    def __init__(self, master_secret: Optional[str] = None):
        self.master_secret = master_secret or secrets.token_urlsafe(32)
        self._keys: Dict[str, APIKey] = {}
        self._lock = threading.Lock()
        
        # Default development key
        self.add_key("dev-key", "dev", rate_limit_rpm=10000)
    
    def add_key(self, name: str, secret: str, rate_limit_rpm: int = 1000,
                allowed_endpoints: Optional[Set[str]] = None) -> str:
        """Create a new API key"""
        key_id = secrets.token_urlsafe(16)
        secret_hash = hashlib.sha256(secret.encode()).hexdigest()
        
        with self._lock:
            self._keys[key_id] = APIKey(
                key_id=key_id,
                secret_hash=secret_hash,
                name=name,
                created_at=datetime.utcnow(),
                rate_limit_rpm=rate_limit_rpm,
                allowed_endpoints=allowed_endpoints
            )
        
        return key_id
    
    def validate_key(self, key_id: str, secret: str) -> bool:
        """Validate API key and secret"""
        with self._lock:
            if key_id not in self._keys:
                return False
            
            api_key = self._keys[key_id]
            
            if not api_key.enabled:
                return False
            
            # Constant-time comparison
            expected_hash = hashlib.sha256(secret.encode()).hexdigest()
            return hmac.compare_digest(api_key.secret_hash, expected_hash)
    
    def get_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key metadata"""
        with self._lock:
            return self._keys.get(key_id)
    
    def update_last_used(self, key_id: str):
        """Update last used timestamp"""
        with self._lock:
            if key_id in self._keys:
                self._keys[key_id].last_used = datetime.utcnow()
    
    def disable_key(self, key_id: str):
        """Disable an API key"""
        with self._lock:
            if key_id in self._keys:
                self._keys[key_id].enabled = False
    
    def list_keys(self) -> Dict[str, Dict[str, Any]]:
        """List all API keys (without secrets)"""
        with self._lock:
            return {
                kid: {
                    "name": key.name,
                    "created_at": key.created_at.isoformat(),
                    "last_used": key.last_used.isoformat() if key.last_used else None,
                    "enabled": key.enabled,
                    "rate_limit_rpm": key.rate_limit_rpm,
                }
                for kid, key in self._keys.items()
            }


class CORSConfig:
    """Secure CORS configuration"""
    
    @staticmethod
    def get_secure_config(allowed_origins: Optional[list] = None,
                         allowed_methods: Optional[list] = None) -> Dict[str, Any]:
        """
        Get secure CORS configuration.
        
        By default: restrict to same-origin, allow only essential methods.
        """
        return {
            "allow_origins": allowed_origins or ["http://localhost:3000", "http://localhost:8000"],
            "allow_credentials": True,
            "allow_methods": allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-API-Key",
                "X-Request-ID",
            ],
            "expose_headers": [
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-Request-ID",
            ],
            "max_age": 600,  # 10 minutes
        }


class SecurityHeaders:
    """Add security headers to responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }


def require_api_key(key_manager: APIKeyManager, rate_limiter: RateLimiter):
    """Decorator to require API key authentication"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Extract API key from header or query param
            api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            
            if not api_key:
                raise HTTPException(
                    status_code=401,
                    detail="API key required (provide via X-API-Key header or ?api_key=...)"
                )
            
            # Parse key_id and secret (format: "key_id:secret")
            if ":" not in api_key:
                raise HTTPException(status_code=401, detail="Invalid API key format")
            
            key_id, secret = api_key.split(":", 1)
            
            # Validate key
            if not key_manager.validate_key(key_id, secret):
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # Check rate limit
            if not rate_limiter.is_allowed(key_id):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": "60"}
                )
            
            # Update last used
            key_manager.update_last_used(key_id)
            
            # Get rate limit stats
            stats = rate_limiter.get_stats(key_id)
            
            # Store in request state
            request.state.api_key_id = key_id
            request.state.rate_limit_stats = stats
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def add_rate_limit_headers(response: JSONResponse, stats: Dict[str, Any]) -> JSONResponse:
    """Add rate limit headers to response"""
    response.headers["X-RateLimit-Limit"] = "1000"
    response.headers["X-RateLimit-Remaining"] = str(stats.get("tokens_remaining", 0))
    return response


class AuditLogger:
    """Log API access for security auditing"""
    
    def __init__(self, log_file: str = "./logs/audit.log"):
        self.log_file = log_file
        self._lock = threading.Lock()
    
    def log_request(self, api_key_id: str, method: str, path: str,
                   status_code: int, user_agent: Optional[str] = None,
                   error: Optional[str] = None):
        """Log API request"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "api_key_id": api_key_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "user_agent": user_agent,
            "error": error,
        }
        
        with self._lock:
            try:
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                print(f"Error writing audit log: {e}")
    
    def get_suspicious_activity(self, hours: int = 1) -> list:
        """Find suspicious activity (rate limit violations, auth failures)"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        suspicious = []
        
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        
                        if entry_time < cutoff:
                            continue
                        
                        # Flagged conditions
                        if entry.get("status_code") in [401, 403, 429]:
                            suspicious.append(entry)
                    except:
                        pass
        except:
            pass
        
        return suspicious


# Global instances (can be overridden in FastAPI app setup)
rate_limiter = RateLimiter(default_rpm=1000)
key_manager = APIKeyManager()
audit_logger = AuditLogger()


if __name__ == "__main__":
    # Test security components
    print("=== Testing API Security Components ===\n")
    
    # Test rate limiter
    print("1. Rate Limiter Test:")
    limiter = RateLimiter(default_rpm=60)  # 1 per second
    client = "test_client"
    
    allowed_count = 0
    for i in range(70):
        if limiter.is_allowed(client):
            allowed_count += 1
    
    print(f"   Allowed 60 requests: {allowed_count == 60}")
    print(f"   Blocked additional: {limiter.is_allowed(client) == False}")
    
    # Test API key manager
    print("\n2. API Key Manager Test:")
    manager = APIKeyManager()
    
    # Create a new key
    secret = "my-secret-password"
    key_id = manager.add_key("test-key", secret, rate_limit_rpm=100)
    print(f"   Created key: {key_id}")
    
    # Validate correct secret
    is_valid = manager.validate_key(key_id, secret)
    print(f"   Valid secret accepted: {is_valid}")
    
    # Validate wrong secret
    is_valid = manager.validate_key(key_id, "wrong-secret")
    print(f"   Wrong secret rejected: {not is_valid}")
    
    # Test CORS
    print("\n3. CORS Configuration:")
    cors_config = CORSConfig.get_secure_config()
    print(f"   Allowed origins: {len(cors_config['allow_origins'])} configured")
    print(f"   Allowed methods: {cors_config['allow_methods']}")
    
    # Test security headers
    print("\n4. Security Headers:")
    headers = SecurityHeaders.get_security_headers()
    print(f"   Security headers: {len(headers)} defined")
    
    print("\nSecurity test complete!")
