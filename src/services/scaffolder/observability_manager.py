"""
Observability and Monitoring for Project Scaffolding

This module handles monitoring, logging, tracing, and health checks
for scaffolded projects using Prometheus, Grafana, ELK stack, and Jaeger.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class MonitoringType(Enum):
    """Types of monitoring supported"""

    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    DATADOG = "datadog"
    NEW_RELIC = "new_relic"
    CLOUDWATCH = "cloudwatch"


class LoggingType(Enum):
    """Types of logging supported"""

    ELK = "elk"  # Elasticsearch, Logstash, Kibana
    EFK = "efk"  # Elasticsearch, Fluentd, Kibana
    LOKI = "loki"  # Grafana Loki
    CLOUDWATCH_LOGS = "cloudwatch_logs"
    SPLUNK = "splunk"


class TracingType(Enum):
    """Types of tracing supported"""

    JAEGER = "jaeger"
    ZIPKIN = "zipkin"
    OPENTELEMETRY = "opentelemetry"
    XRAY = "xray"  # AWS X-Ray
    CLOUD_TRACE = "cloud_trace"  # GCP Cloud Trace


class ObservabilityFeature(Enum):
    """Observability features that can be implemented"""

    MONITORING = "monitoring"
    LOGGING = "logging"
    TRACING = "tracing"
    METRICS = "metrics"
    HEALTH_CHECKS = "health_checks"
    ALERTING = "alerting"
    DASHBOARDS = "dashboards"


@dataclass
class ObservabilityConfig:
    """Observability configuration"""

    features: List[ObservabilityFeature]
    monitoring_type: Optional[MonitoringType] = None
    logging_type: Optional[LoggingType] = None
    tracing_type: Optional[TracingType] = None
    enable_health_checks: bool = True
    enable_metrics: bool = True
    enable_structured_logging: bool = True
    log_level: str = "INFO"
    metrics_port: int = 9090
    health_check_port: int = 8080


class ObservabilityManager:
    """
    Manages observability features including monitoring, logging,
    tracing, and health checks for scaffolded projects.
    """

    def __init__(self):
        self.templates = {
            "python": {
                "fastapi": self._get_python_fastapi_observability,
                "flask": self._get_python_flask_observability,
                "django": self._get_python_django_observability,
            },
            "javascript": {
                "express": self._get_javascript_express_observability,
                "fastify": self._get_javascript_fastify_observability,
            },
            "java": {
                "spring": self._get_java_spring_observability,
            },
        }

    async def generate_observability_setup(
        self,
        project_path: Path,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
        monitoring_type: MonitoringType = MonitoringType.PROMETHEUS,
        logging_type: LoggingType = LoggingType.ELK,
        tracing_type: TracingType = TracingType.JAEGER,
        observability_features: Optional[List[ObservabilityFeature]] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive observability setup for a project.

        Args:
            project_path: Path to the project directory
            language: Programming language (python, javascript, etc.)
            framework: Framework being used
            features: List of features to include
            monitoring_type: Type of monitoring to implement
            logging_type: Type of logging to implement
            tracing_type: Type of tracing to implement
            observability_features: List of observability features to implement

        Returns:
            Dictionary containing generated observability files and their paths
        """
        if observability_features is None:
            observability_features = [
                ObservabilityFeature.MONITORING,
                ObservabilityFeature.LOGGING,
                ObservabilityFeature.TRACING,
                ObservabilityFeature.METRICS,
                ObservabilityFeature.HEALTH_CHECKS,
            ]

        # Create observability configuration
        observability_config = ObservabilityConfig(
            features=observability_features,
            monitoring_type=monitoring_type,
            logging_type=logging_type,
            tracing_type=tracing_type,
        )

        generated_files = {}

        # Generate language/framework specific observability code
        if language.lower() in self.templates:
            lang_templates = self.templates[language.lower()]
            if framework and framework.lower() in lang_templates:
                template_func = lang_templates[framework.lower()]
                files = await template_func(
                    project_path, observability_config, features
                )
                generated_files.update(files)

        # Generate common observability files
        common_files = await self._generate_common_observability_files(
            project_path, observability_config, language, framework
        )
        generated_files.update(common_files)

        return generated_files

    async def _generate_common_observability_files(
        self,
        project_path: Path,
        observability_config: ObservabilityConfig,
        language: str,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate common observability files applicable to all languages/frameworks"""
        generated_files = {}

        # Generate observability configuration file
        config_file = project_path / "observability_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            config_data = {
                "features": [f.value for f in observability_config.features],
                "monitoring": {
                    "type": (
                        observability_config.monitoring_type.value
                        if observability_config.monitoring_type
                        else None
                    ),
                    "metrics_port": observability_config.metrics_port,
                },
                "logging": {
                    "type": (
                        observability_config.logging_type.value
                        if observability_config.logging_type
                        else None
                    ),
                    "level": observability_config.log_level,
                    "structured": observability_config.enable_structured_logging,
                },
                "tracing": {
                    "type": (
                        observability_config.tracing_type.value
                        if observability_config.tracing_type
                        else None
                    ),
                },
                "health_checks": {
                    "enabled": observability_config.enable_health_checks,
                    "port": observability_config.health_check_port,
                },
                "language": language,
                "framework": framework,
            }
            json.dump(config_data, f, indent=2)

        generated_files["observability_config"] = {
            "path": "observability_config.json",
            "description": "Observability configuration file with all monitoring settings",
        }

        # Generate docker-compose for monitoring stack
        if observability_config.monitoring_type == MonitoringType.PROMETHEUS:
            docker_compose = project_path / "docker-compose.monitoring.yml"
            with open(docker_compose, "w", encoding="utf-8") as f:
                f.write(self._generate_prometheus_docker_compose())
            generated_files["docker_compose_monitoring"] = {
                "path": "docker-compose.monitoring.yml",
                "description": "Docker Compose configuration for monitoring stack",
            }

        # Generate Prometheus configuration
        if observability_config.monitoring_type == MonitoringType.PROMETHEUS:
            prometheus_config = project_path / "monitoring" / "prometheus.yml"
            prometheus_config.parent.mkdir(parents=True, exist_ok=True)
            with open(prometheus_config, "w", encoding="utf-8") as f:
                f.write(self._generate_prometheus_config())
            generated_files["prometheus_config"] = {
                "path": "monitoring/prometheus.yml",
                "description": "Prometheus configuration file",
            }

        # Generate Grafana dashboards
        if observability_config.monitoring_type == MonitoringType.GRAFANA:
            grafana_dashboards = project_path / "monitoring" / "dashboards"
            grafana_dashboards.mkdir(parents=True, exist_ok=True)

            # Application dashboard
            app_dashboard = grafana_dashboards / "application.json"
            with open(app_dashboard, "w", encoding="utf-8") as f:
                f.write(self._generate_grafana_app_dashboard())
            generated_files["grafana_app_dashboard"] = {
                "path": "monitoring/dashboards/application.json",
                "description": "Grafana application dashboard",
            }

            # System dashboard
            system_dashboard = grafana_dashboards / "system.json"
            with open(system_dashboard, "w", encoding="utf-8") as f:
                f.write(self._generate_grafana_system_dashboard())
            generated_files["grafana_system_dashboard"] = {
                "path": "monitoring/dashboards/system.json",
                "description": "Grafana system dashboard",
            }

        # Generate logging configuration
        if observability_config.logging_type == LoggingType.ELK:
            logstash_config = project_path / "logging" / "logstash.conf"
            logstash_config.parent.mkdir(parents=True, exist_ok=True)
            with open(logstash_config, "w", encoding="utf-8") as f:
                f.write(self._generate_logstash_config())
            generated_files["logstash_config"] = {
                "path": "logging/logstash.conf",
                "description": "Logstash configuration for ELK stack",
            }

        # Generate Jaeger configuration
        if observability_config.tracing_type == TracingType.JAEGER:
            jaeger_config = project_path / "tracing" / "jaeger-config.yml"
            jaeger_config.parent.mkdir(parents=True, exist_ok=True)
            with open(jaeger_config, "w", encoding="utf-8") as f:
                f.write(self._generate_jaeger_config())
            generated_files["jaeger_config"] = {
                "path": "tracing/jaeger-config.yml",
                "description": "Jaeger tracing configuration",
            }

        return generated_files

    def _generate_prometheus_docker_compose(self) -> str:
        """Generate Docker Compose for Prometheus monitoring stack"""
        return """version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    depends_on:
      - prometheus
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
"""

    def _generate_prometheus_config(self) -> str:
        """Generate Prometheus configuration"""
        return """global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'application'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
"""

    def _generate_grafana_app_dashboard(self) -> str:
        """Generate Grafana application dashboard JSON"""
        return """{
  "dashboard": {
    "id": null,
    "title": "Application Metrics",
    "tags": ["application", "metrics"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "HTTP Request Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}"""

    def _generate_grafana_system_dashboard(self) -> str:
        """Generate Grafana system dashboard JSON"""
        return """{
  "dashboard": {
    "id": null,
    "title": "System Metrics",
    "tags": ["system", "metrics"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU Usage %"
          }
        ]
      },
      {
        "id": 2,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
            "legendFormat": "Memory Usage %"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}"""

    def _generate_logstash_config(self) -> str:
        """Generate Logstash configuration"""
        return """input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  json {
    source => "message"
  }

  date {
    match => ["timestamp", "ISO8601"]
  }

  mutate {
    remove_field => ["message"]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "application-logs-%{+YYYY.MM.dd}"
  }

  stdout {
    codec => rubydebug
  }
}"""

    def _generate_jaeger_config(self) -> str:
        """Generate Jaeger configuration"""
        return """service:
  extensions:
    - jaeger_storage
    - jaeger_query
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger_storage]
  telemetry:
    logs:
      level: "debug"

extensions:
  jaeger_storage:
    backends:
      memory:
        max_traces: 100000

  jaeger_query:
    storage:
      traces: jaeger_storage

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  jaeger_storage:
    trace_storage: jaeger_storage
"""

    async def _get_python_fastapi_observability(
        self,
        project_path: Path,
        observability_config: ObservabilityConfig,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate Python FastAPI observability implementation"""
        generated_files = {}

        # Generate monitoring middleware
        if ObservabilityFeature.MONITORING in observability_config.features:
            monitoring_file = project_path / "src" / "middleware" / "monitoring.py"
            monitoring_file.parent.mkdir(parents=True, exist_ok=True)

            monitoring_code = self._generate_fastapi_monitoring_middleware(
                observability_config
            )
            with open(monitoring_file, "w", encoding="utf-8") as f:
                f.write(monitoring_code)

            generated_files["monitoring_middleware"] = {
                "path": "src/middleware/monitoring.py",
                "description": "Monitoring middleware with Prometheus metrics",
            }

        # Generate logging configuration
        if ObservabilityFeature.LOGGING in observability_config.features:
            logging_file = project_path / "src" / "core" / "logging.py"
            logging_file.parent.mkdir(parents=True, exist_ok=True)

            logging_code = self._generate_python_structured_logging(
                observability_config
            )
            with open(logging_file, "w", encoding="utf-8") as f:
                f.write(logging_code)

            generated_files["logging_config"] = {
                "path": "src/core/logging.py",
                "description": "Structured logging configuration",
            }

        # Generate tracing middleware
        if ObservabilityFeature.TRACING in observability_config.features:
            tracing_file = project_path / "src" / "middleware" / "tracing.py"
            tracing_file.parent.mkdir(parents=True, exist_ok=True)

            tracing_code = self._generate_fastapi_tracing_middleware(
                observability_config
            )
            with open(tracing_file, "w", encoding="utf-8") as f:
                f.write(tracing_code)

            generated_files["tracing_middleware"] = {
                "path": "src/middleware/tracing.py",
                "description": "Distributed tracing middleware",
            }

        # Generate health check endpoints
        if ObservabilityFeature.HEALTH_CHECKS in observability_config.features:
            health_file = project_path / "src" / "routes" / "health.py"
            health_file.parent.mkdir(parents=True, exist_ok=True)

            health_code = self._generate_fastapi_health_routes(observability_config)
            with open(health_file, "w", encoding="utf-8") as f:
                f.write(health_code)

            generated_files["health_routes"] = {
                "path": "src/routes/health.py",
                "description": "Health check endpoints",
            }

        # Generate metrics endpoints
        if ObservabilityFeature.METRICS in observability_config.features:
            metrics_file = project_path / "src" / "routes" / "metrics.py"
            metrics_file.parent.mkdir(parents=True, exist_ok=True)

            metrics_code = self._generate_fastapi_metrics_routes(observability_config)
            with open(metrics_file, "w", encoding="utf-8") as f:
                f.write(metrics_code)

            generated_files["metrics_routes"] = {
                "path": "src/routes/metrics.py",
                "description": "Metrics endpoints for Prometheus",
            }

        # Generate requirements for observability
        requirements_obs = project_path / "requirements-observability.txt"
        with open(requirements_obs, "w", encoding="utf-8") as f:
            f.write("prometheus-client>=0.17.0\n")
            f.write("structlog>=23.1.0\n")
            f.write("opentelemetry-distro>=0.40b0\n")
            f.write("opentelemetry-instrumentation-fastapi>=0.40b0\n")
            f.write("opentelemetry-exporter-jaeger>=1.20.0\n")
            f.write("opentelemetry-exporter-otlp>=1.20.0\n")
            f.write("rich>=13.0.0\n")
            f.write("loguru>=0.7.0\n")

        generated_files["requirements_observability"] = {
            "path": "requirements-observability.txt",
            "description": "Observability dependencies",
        }

        return generated_files

    def _generate_fastapi_monitoring_middleware(
        self, observability_config: ObservabilityConfig
    ) -> str:
        """Generate FastAPI monitoring middleware with Prometheus"""
        return '''"""
Monitoring middleware with Prometheus metrics
"""

import time
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil
from typing import Callable

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Number of active HTTP requests'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'Current CPU usage percentage'
)

MEMORY_USAGE = Gauge(
    'memory_usage_percent',
    'Current memory usage percentage'
)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics"""

    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/metrics", "/health"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        ACTIVE_REQUESTS.inc()

        start_time = time.time()

        try:
            response = await call_next(request)

            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(time.time() - start_time)

            return response

        finally:
            ACTIVE_REQUESTS.dec()

def update_system_metrics():
    """Update system metrics"""
    CPU_USAGE.set(psutil.cpu_percent(interval=1))
    MEMORY_USAGE.set(psutil.virtual_memory().percent)

# System metrics collector
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(update_system_metrics, 'interval', seconds=30)
scheduler.start()
'''

    def _generate_python_structured_logging(
        self, observability_config: ObservabilityConfig
    ) -> str:
        """Generate structured logging configuration"""
        return '''"""
Structured logging configuration
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict
import structlog
from pythonjsonlogger import jsonlogger

def setup_logging(
    log_level: str = "INFO",
    log_file: str = "app.log",
    enable_json: bool = True
) -> None:
    """Setup structured logging"""

    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )

    # Configure structlog
    if enable_json:
        # JSON logging for production
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                jsonlogger.JsonFormatter(),
                structlog.write_to_file(log_file + ".jsonl"),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # Human-readable logging for development
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

def get_logger(name: str) -> Any:
    """Get a configured logger instance"""
    return structlog.get_logger(name)

# Global logger instance
logger = get_logger(__name__)
'''

    def _generate_fastapi_tracing_middleware(
        self, observability_config: ObservabilityConfig
    ) -> str:
        """Generate FastAPI tracing middleware"""
        return '''"""
Distributed tracing middleware
"""

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import time

# Setup tracing
def setup_tracing(service_name: str = "fastapi-app"):
    """Setup OpenTelemetry tracing"""

    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider())

    # Set up Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )

    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Instrument FastAPI
    FastAPIInstrumentor().instrument()

    return trace.get_tracer(__name__)

class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed tracing"""

    def __init__(self, app, tracer=None):
        super().__init__(app)
        self.tracer = tracer or setup_tracing()

    async def dispatch(self, request: Request, call_next):
        with self.tracer.start_as_span(
            f"{request.method} {request.url.path}",
            kind=trace.SpanKind.SERVER
        ) as span:
            # Add request attributes to span
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.headers.get("host", ""))

            # Add custom attributes
            if hasattr(request.state, 'user_id'):
                span.set_attribute("user.id", request.state.user_id)

            start_time = time.time()

            try:
                response = await call_next(request)

                # Add response attributes
                span.set_attribute("http.status_code", response.status_code)
                span.set_status(trace.Status(trace.StatusCode.OK))

                return response

            except Exception as exc:
                # Record exception
                span.record_exception(exc)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
                raise

            finally:
                # Record duration
                duration = time.time() - start_time
                span.set_attribute("http.duration", duration)
'''

    def _generate_fastapi_health_routes(
        self, observability_config: ObservabilityConfig
    ) -> str:
        """Generate FastAPI health check routes"""
        return '''"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
import psutil
import time
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime: float
    version: str = "1.0.0"

class DetailedHealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime: float
    version: str
    services: Dict[str, Any]
    system: Dict[str, Any]

# Application start time
START_TIME = time.time()

@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        uptime=time.time() - START_TIME
    )

@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check with system and service status"""

    # Check system resources
    system_info = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }

    # Check services (mock implementations - replace with real checks)
    services_status = {
        "database": await check_database_health(),
        "cache": await check_cache_health(),
        "external_api": await check_external_api_health(),
    }

    # Determine overall status
    all_services_healthy = all(service.get("status") == "healthy"
                              for service in services_status.values())
    overall_status = "healthy" if all_services_healthy else "unhealthy"

    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        uptime=time.time() - START_TIME,
        services=services_status,
        system=system_info
    )

@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    # Check if application is ready to serve traffic
    # This might include database connections, cache availability, etc.
    return {"status": "ready"}

@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    # Check if application is running and not deadlocked
    return {"status": "alive"}

async def check_database_health() -> Dict[str, Any]:
    """Check database health"""
    try:
        # Replace with actual database health check
        # Example: await database.execute("SELECT 1")
        return {"status": "healthy", "response_time": 0.001}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_cache_health() -> Dict[str, Any]:
    """Check cache health"""
    try:
        # Replace with actual cache health check
        # Example: await redis.ping()
        return {"status": "healthy", "response_time": 0.001}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_external_api_health() -> Dict[str, Any]:
    """Check external API health"""
    try:
        # Replace with actual external API health check
        # Example: response = await httpx.get("https://api.example.com/health")
        return {"status": "healthy", "response_time": 0.1}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
'''

    def _generate_fastapi_metrics_routes(
        self, observability_config: ObservabilityConfig
    ) -> str:
        """Generate FastAPI metrics routes"""
        return '''"""
Metrics endpoints for Prometheus
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@router.get("/health")
async def metrics_health():
    """Health check for metrics endpoint"""
    return {"status": "metrics_endpoint_healthy"}
'''

    # Placeholder methods for other frameworks - can be expanded later
    async def _get_python_flask_observability(self, *args, **kwargs):
        return {}

    async def _get_python_django_observability(self, *args, **kwargs):
        return {}

    async def _get_javascript_express_observability(self, *args, **kwargs):
        return {}

    async def _get_javascript_fastify_observability(self, *args, **kwargs):
        return {}

    async def _get_java_spring_observability(self, *args, **kwargs):
        return {}
