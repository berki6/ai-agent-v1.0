"""
Security and Authentication Management for Project Scaffolding

This module handles authentication, authorization, input validation,
rate limiting, and security headers for scaffolded projects.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class AuthType(Enum):
    """Types of authentication supported"""

    JWT = "jwt"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    API_KEY = "api_key"
    SESSION = "session"
    NONE = "none"


class SecurityFeature(Enum):
    """Security features that can be implemented"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    RATE_LIMITING = "rate_limiting"
    SECURITY_HEADERS = "security_headers"
    CORS = "cors"
    CSRF_PROTECTION = "csrf_protection"
    ENCRYPTION = "encryption"
    AUDIT_LOGGING = "audit_logging"


@dataclass
class AuthConfig:
    """Authentication configuration"""

    auth_type: AuthType
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    oauth_providers: Optional[List[str]] = None
    api_key_header: str = "X-API-Key"
    session_secret: Optional[str] = None
    basic_auth_users: Optional[Dict[str, str]] = None


@dataclass
class SecurityConfig:
    """Security configuration"""

    features: List[SecurityFeature]
    auth_config: Optional[AuthConfig] = None
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    cors_origins: Optional[List[str]] = None
    security_headers: Optional[Dict[str, str]] = None
    input_validation_strict: bool = True


class SecurityManager:
    """
    Manages security features including authentication, authorization,
    input validation, rate limiting, and security headers.
    """

    def __init__(self):
        self.templates = {
            "python": {
                "fastapi": self._get_fastapi_security_template,
                "flask": self._get_flask_security_template,
                "django": self._get_django_security_template,
            },
            "javascript": {
                "express": self._get_express_security_template,
                "fastify": self._get_fastify_security_template,
            },
            "java": {
                "spring": self._get_spring_security_template,
            },
        }

    async def generate_security_config(
        self,
        project_path: Path,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
        auth_type: AuthType = AuthType.JWT,
        security_features: Optional[List[SecurityFeature]] = None,
    ) -> Dict[str, Any]:
        """
        Generate security configuration and code for a project.

        Args:
            project_path: Path to the project directory
            language: Programming language (python, javascript, etc.)
            framework: Framework being used (fastapi, express, etc.)
            features: List of features to include
            auth_type: Type of authentication to implement
            security_features: List of security features to implement

        Returns:
            Dictionary containing generated security files and their paths
        """
        if security_features is None:
            security_features = [
                SecurityFeature.AUTHENTICATION,
                SecurityFeature.INPUT_VALIDATION,
                SecurityFeature.SECURITY_HEADERS,
                SecurityFeature.CORS,
            ]

        # Create security configuration
        security_config = SecurityConfig(
            features=security_features,
            auth_config=AuthConfig(auth_type=auth_type),
        )

        generated_files = {}

        # Generate language/framework specific security code
        if language.lower() in self.templates:
            lang_templates = self.templates[language.lower()]
            if framework and framework.lower() in lang_templates:
                template_func = lang_templates[framework.lower()]
                files = await template_func(project_path, security_config, features)
                generated_files.update(files)

        # Generate common security files
        common_files = await self._generate_common_security_files(
            project_path, security_config, language, framework
        )
        generated_files.update(common_files)

        return generated_files

    async def _generate_common_security_files(
        self,
        project_path: Path,
        security_config: SecurityConfig,
        language: str,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate common security files applicable to all languages/frameworks"""
        generated_files = {}

        # Generate security configuration file
        config_file = project_path / "security_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            config_data = {
                "features": [f.value for f in security_config.features],
                "authentication": (
                    {
                        "type": (
                            security_config.auth_config.auth_type.value
                            if security_config.auth_config
                            else None
                        ),
                        "jwt_expiration_hours": (
                            security_config.auth_config.jwt_expiration_hours
                            if security_config.auth_config
                            else None
                        ),
                    }
                    if security_config.auth_config
                    else None
                ),
                "rate_limiting": {
                    "requests": security_config.rate_limit_requests,
                    "window_seconds": security_config.rate_limit_window_seconds,
                },
                "cors": {
                    "origins": security_config.cors_origins or ["*"],
                },
                "security_headers": security_config.security_headers
                or self._get_default_security_headers(),
            }
            json.dump(config_data, f, indent=2)

        generated_files["security_config"] = {
            "path": "security_config.json",
            "description": "Security configuration file with all security settings",
        }

        # Generate .env security variables
        env_security = project_path / ".env.security"
        with open(env_security, "w", encoding="utf-8") as f:
            f.write("# Security Environment Variables\n")
            f.write("# Add these to your main .env file\n\n")

            if security_config.auth_config:
                if security_config.auth_config.auth_type == AuthType.JWT:
                    f.write("# JWT Configuration\n")
                    f.write("JWT_SECRET_KEY=your_jwt_secret_key_here\n")
                    f.write("JWT_ALGORITHM=HS256\n")
                    f.write("JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30\n")
                    f.write("JWT_REFRESH_TOKEN_EXPIRE_DAYS=7\n")

                if security_config.auth_config.auth_type == AuthType.OAUTH2:
                    f.write("# OAuth2 Configuration\n")
                    f.write("OAUTH_CLIENT_ID=your_oauth_client_id\n")
                    f.write("OAUTH_CLIENT_SECRET=your_oauth_client_secret\n")
                    f.write("OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback\n")

                if security_config.auth_config.auth_type == AuthType.API_KEY:
                    f.write("# API Key Configuration\n")
                    f.write("API_KEY_HEADER=X-API-Key\n")
                    f.write("API_KEY=your_api_key_here\n")

            if SecurityFeature.RATE_LIMITING in security_config.features:
                f.write("# Rate Limiting\n")
                f.write(f"RATE_LIMIT_REQUESTS={security_config.rate_limit_requests}\n")
                f.write(
                    f"RATE_LIMIT_WINDOW_SECONDS={security_config.rate_limit_window_seconds}\n"
                )

        generated_files["env_security"] = {
            "path": ".env.security",
            "description": "Security environment variables template",
        }

        return generated_files

    def _get_default_security_headers(self) -> Dict[str, str]:
        """Get default security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

    async def _get_fastapi_security_template(
        self,
        project_path: Path,
        security_config: SecurityConfig,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate FastAPI security implementation"""
        generated_files = {}

        # Generate authentication middleware
        if SecurityFeature.AUTHENTICATION in security_config.features:
            auth_file = project_path / "src" / "auth.py"
            auth_file.parent.mkdir(parents=True, exist_ok=True)

            auth_code = self._generate_fastapi_auth_code(security_config)
            with open(auth_file, "w", encoding="utf-8") as f:
                f.write(auth_code)

            generated_files["auth_module"] = {
                "path": "src/auth.py",
                "description": "Authentication module with JWT/OAuth2 support",
            }

        # Generate security middleware
        security_file = project_path / "src" / "middleware" / "security.py"
        security_file.parent.mkdir(parents=True, exist_ok=True)

        security_code = self._generate_fastapi_security_middleware(security_config)
        with open(security_file, "w", encoding="utf-8") as f:
            f.write(security_code)

        generated_files["security_middleware"] = {
            "path": "src/middleware/security.py",
            "description": "Security middleware with headers, CORS, and rate limiting",
        }

        # Generate models
        if SecurityFeature.AUTHENTICATION in security_config.features:
            models_file = project_path / "src" / "models" / "auth.py"
            models_file.parent.mkdir(parents=True, exist_ok=True)

            models_code = self._generate_fastapi_auth_models()
            with open(models_file, "w", encoding="utf-8") as f:
                f.write(models_code)

            generated_files["auth_models"] = {
                "path": "src/models/auth.py",
                "description": "Authentication models and schemas",
            }

        # Generate routes
        if SecurityFeature.AUTHENTICATION in security_config.features:
            routes_file = project_path / "src" / "routes" / "auth.py"
            routes_file.parent.mkdir(parents=True, exist_ok=True)

            routes_code = self._generate_fastapi_auth_routes(security_config)
            with open(routes_file, "w", encoding="utf-8") as f:
                f.write(routes_code)

            generated_files["auth_routes"] = {
                "path": "src/routes/auth.py",
                "description": "Authentication routes for login/logout",
            }

        return generated_files

    def _generate_fastapi_auth_code(self, security_config: SecurityConfig) -> str:
        """Generate FastAPI authentication code"""
        auth_type = (
            security_config.auth_config.auth_type
            if security_config.auth_config
            else AuthType.NONE
        )

        code = '''"""
Authentication utilities for FastAPI application
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
'''

        if auth_type == AuthType.JWT:
            code += '''
# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Here you would typically fetch user from database
    # For now, return a mock user
    return {"username": username, "user_id": 1}

def authenticate_user(username: str, password: str):
    """Authenticate a user (mock implementation)"""
    # This is a mock - in real app, check against database
    if username == "admin" and password == "admin":
        return {"username": username, "user_id": 1}
    return False
'''

        elif auth_type == AuthType.API_KEY:
            code += '''
# API Key Configuration
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
VALID_API_KEYS = os.getenv("API_KEY", "").split(",") if os.getenv("API_KEY") else []

def verify_api_key(api_key: str = Depends(HTTPBearer())):
    """Verify API key"""
    if api_key.credentials not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key.credentials
'''

        return code

    def _generate_fastapi_security_middleware(
        self, security_config: SecurityConfig
    ) -> str:
        """Generate FastAPI security middleware"""
        code = '''"""
Security middleware for FastAPI application
"""

import os
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
from typing import Dict

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        # Clean old requests
        current_time = time.time()
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json"
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response

# CORS configuration
def get_cors_middleware():
    """Get CORS middleware configuration"""
    return CORSMiddleware(
        allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
'''

        return code

    def _generate_fastapi_auth_models(self) -> str:
        """Generate FastAPI authentication models"""
        return '''"""
Authentication models and schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    user_id: int

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
'''

    def _generate_fastapi_auth_routes(self, security_config: SecurityConfig) -> str:
        """Generate FastAPI authentication routes"""
        auth_type = (
            security_config.auth_config.auth_type
            if security_config.auth_config
            else AuthType.NONE
        )

        code = '''"""
Authentication routes for FastAPI application
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
'''

        if auth_type == AuthType.JWT:
            code += '''
from ..auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user
)
from ..models.auth import Token, LoginRequest, RefreshTokenRequest, User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user["username"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    # In a real implementation, validate refresh token and issue new access token
    # This is a simplified version
    return {
        "access_token": "new_access_token",
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint"""
    # In a real implementation, you might want to blacklist the token
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
'''

        elif auth_type == AuthType.API_KEY:
            code += '''
from ..auth import verify_api_key

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/verify")
async def verify_api_key_endpoint(api_key: str = Depends(verify_api_key)):
    """Verify API key endpoint"""
    return {"message": "API key is valid", "key": api_key}
'''

        return code

    # Placeholder methods for other frameworks - can be expanded later
    async def _get_flask_security_template(self, *args, **kwargs):
        return {}

    async def _get_django_security_template(self, *args, **kwargs):
        return {}

    async def _get_express_security_template(self, *args, **kwargs):
        return {}

    async def _get_fastify_security_template(self, *args, **kwargs):
        return {}

    async def _get_spring_security_template(self, *args, **kwargs):
        return {}
