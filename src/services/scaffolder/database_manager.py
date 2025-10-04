"""
Database Integration Manager for Scaffolder

This module provides comprehensive database integration capabilities for scaffolded projects,
including support for PostgreSQL, MySQL, MongoDB, Redis, and database migration tools.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...core.ai_utils import AIUtils


from enum import Enum


class DatabaseType(Enum):
    """Supported database types"""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    SQLITE = "sqlite"


class MigrationTool(Enum):
    """Supported database migration tools"""

    ALEMBIC = "alembic"
    FLYWAY = "flyway"
    LIQUIBASE = "liquibase"
    MONGOOSE = "mongoose"
    CUSTOM = "custom"


class ORMType(Enum):
    """Supported ORM/Object-Document Mapper types"""

    SQLALCHEMY = "sqlalchemy"
    DJANGO_ORM = "django_orm"
    MONGOENGINE = "mongoengine"
    PYMONGO = "pymongo"
    REDIS_PY = "redis_py"
    CUSTOM = "custom"


class DatabaseFeature(Enum):
    """Database integration features"""

    CONNECTION_POOLING = "connection_pooling"
    MIGRATIONS = "migrations"
    SEEDING = "seeding"
    BACKUP_RESTORE = "backup_restore"
    MONITORING = "monitoring"
    CACHING = "caching"
    REPLICATION = "replication"


class DatabaseConfig(BaseModel):
    """Database configuration model"""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(description="Database port")
    database: str = Field(description="Database name")
    username: str = Field(description="Database username")
    password: str = Field(description="Database password")
    ssl_mode: str = Field(default="prefer", description="SSL mode for connections")
    connection_pool_size: int = Field(default=10, description="Connection pool size")
    connection_timeout: int = Field(
        default=30, description="Connection timeout in seconds"
    )


class DatabaseManager:
    """
    Manager for database integration setup and configuration
    """

    def __init__(self):
        self.ai_utils = AIUtils()

    async def generate_database_setup(
        self,
        project_path: Path,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
        database_type: DatabaseType = DatabaseType.POSTGRESQL,
        orm_type: Optional[ORMType] = None,
        migration_tool: Optional[MigrationTool] = None,
        database_features: Optional[List[DatabaseFeature]] = None,
        database_config: Optional[DatabaseConfig] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive database integration setup

        Args:
            project_path: Path to the project root
            language: Programming language (python, javascript, etc.)
            framework: Web framework being used
            features: List of project features
            database_type: Type of database to integrate
            orm_type: ORM/Object-Document Mapper to use
            migration_tool: Database migration tool
            database_features: List of database features to enable
            database_config: Database configuration settings

        Returns:
            Dictionary containing generated database files and configurations
        """

        # Set defaults based on database type
        if orm_type is None:
            if database_type == DatabaseType.POSTGRESQL:
                orm_type = ORMType.SQLALCHEMY
            elif database_type == DatabaseType.MONGODB:
                orm_type = ORMType.PYMONGO
            elif database_type == DatabaseType.REDIS:
                orm_type = ORMType.REDIS_PY
            else:
                orm_type = ORMType.SQLALCHEMY

        if migration_tool is None:
            if database_type in [
                DatabaseType.POSTGRESQL,
                DatabaseType.MYSQL,
                DatabaseType.SQLITE,
            ]:
                migration_tool = MigrationTool.ALEMBIC
            elif database_type == DatabaseType.MONGODB:
                migration_tool = MigrationTool.MONGOOSE
            else:
                migration_tool = MigrationTool.CUSTOM

        if database_features is None:
            database_features = [
                DatabaseFeature.CONNECTION_POOLING,
                DatabaseFeature.MIGRATIONS,
                DatabaseFeature.SEEDING,
            ]

        if database_config is None:
            database_config = self._get_default_config(database_type)

        # Generate database integration files
        generated_files = {}

        # Generate database configuration
        config_files = await self._generate_database_config(
            project_path, language, database_type, database_config
        )
        generated_files.update(config_files)

        # Generate ORM/Models setup
        orm_files = await self._generate_orm_setup(
            project_path, language, framework, database_type, orm_type
        )
        generated_files.update(orm_files)

        # Generate migration setup
        migration_files = await self._generate_migration_setup(
            project_path, language, database_type, migration_tool
        )
        generated_files.update(migration_files)

        # Generate database utilities
        utility_files = await self._generate_database_utilities(
            project_path, language, database_type, database_features
        )
        generated_files.update(utility_files)

        # Generate Docker setup for database
        docker_files = await self._generate_database_docker(
            project_path, database_type, database_config
        )
        generated_files.update(docker_files)

        return generated_files

    async def _generate_database_config(
        self,
        project_path: Path,
        language: str,
        database_type: DatabaseType,
        config: DatabaseConfig,
    ) -> Dict[str, Any]:
        """Generate database configuration files"""

        files = {}

        if language.lower() == "python":
            # Generate Python database configuration
            config_content = f'''"""
Database Configuration
Auto-generated by Scaffolder Database Manager
"""

import os
from typing import Optional

from pydantic import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database settings loaded from environment variables"""

    # Database connection settings
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None

    # Connection settings
    DB_SSL_MODE: Optional[str] = None
    DB_POOL_SIZE: Optional[int] = None
    DB_TIMEOUT: Optional[int] = None

    # Additional settings
    DB_ECHO: bool = False  # Set to True for SQL query logging
    DB_MAX_OVERFLOW: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, database_type: str = "postgresql", **kwargs):
        super().__init__(**kwargs)
        self._database_type = database_type

    @property
    def database_url(self) -> str:
        """Generate database URL based on database type"""
        if self._database_type == "postgresql":
            return "postgresql://%s:%s@%s:%s/%s" % (self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_NAME)
        elif self._database_type == "mysql":
            return "mysql+pymysql://%s:%s@%s:%s/%s" % (self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_NAME)
        elif self._database_type == "mongodb":
            return "mongodb://%s:%s@%s:%s/%s" % (self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_NAME)
        elif self._database_type == "redis":
            return "redis://%s:%s@%s:%s" % (self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT)
        else:
            return "sqlite:///./%s.db" % self.DB_NAME


# Global database settings instance
database_settings = DatabaseSettings(
    database_type="{database_type.value}",
    DB_HOST="{config.host}",
    DB_PORT={config.port},
    DB_NAME="{config.database}",
    DB_USER="{config.username}",
    DB_PASSWORD="{config.password}",
    DB_SSL_MODE="{config.ssl_mode}",
    DB_POOL_SIZE={config.connection_pool_size},
    DB_TIMEOUT={config.connection_timeout}
)
'''

            files["src/config/database.py"] = config_content

            # Generate .env template
            env_content = f"""# Database Configuration
# Auto-generated by Scaffolder Database Manager

DB_HOST={config.host}
DB_PORT={config.port}
DB_NAME={config.database}
DB_USER={config.username}
DB_PASSWORD={config.password}
DB_SSL_MODE={config.ssl_mode}
DB_POOL_SIZE={config.connection_pool_size}
DB_TIMEOUT={config.connection_timeout}
DB_ECHO=false
"""

            files[".env.example"] = env_content

        elif language.lower() == "javascript" or language.lower() == "typescript":
            # Generate Node.js/TypeScript database configuration
            config_content = f"""/**
 * Database Configuration
 * Auto-generated by Scaffolder Database Manager
 */

import {{ config }} from 'dotenv';

config();

interface DatabaseConfig {{
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl: boolean;
  poolSize: number;
  timeout: number;
}}

const databaseConfig: DatabaseConfig = {{
  host: process.env.DB_HOST || '{config.host}',
  port: parseInt(process.env.DB_PORT || '{config.port}'),
  database: process.env.DB_NAME || '{config.database}',
  username: process.env.DB_USER || '{config.username}',
  password: process.env.DB_PASSWORD || '{config.password}',
  ssl: process.env.DB_SSL === 'true',
  poolSize: parseInt(process.env.DB_POOL_SIZE || '{config.connection_pool_size}'),
  timeout: parseInt(process.env.DB_TIMEOUT || '{config.connection_timeout}'),
}};

export const getDatabaseUrl = (): string => {{
  if ('{database_type.value}' === 'mongodb') {{
    return `mongodb://${{databaseConfig.username}}:${{databaseConfig.password}}@${{databaseConfig.host}}:${{databaseConfig.port}}/${{databaseConfig.database}}`;
  }} else if ('{database_type.value}' === 'redis') {{
    return `redis://${{databaseConfig.username}}:${{databaseConfig.password}}@${{databaseConfig.host}}:${{databaseConfig.port}}`;
  }} else {{
    return `postgres://${{databaseConfig.username}}:${{databaseConfig.password}}@${{databaseConfig.host}}:${{databaseConfig.port}}/${{databaseConfig.database}}`;
  }}
}};

export default databaseConfig;
"""

            files["src/config/database.ts"] = config_content

        return files

    async def _generate_orm_setup(
        self,
        project_path: Path,
        language: str,
        framework: Optional[str],
        database_type: DatabaseType,
        orm_type: ORMType,
    ) -> Dict[str, Any]:
        """Generate ORM/Models setup"""

        files = {}

        if language.lower() == "python":
            if orm_type == ORMType.SQLALCHEMY:
                # Generate SQLAlchemy models and setup
                base_model_content = '''"""
Base Database Models
Auto-generated by Scaffolder Database Manager
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..config.database import database_settings

# Create database engine
engine = create_engine(
    database_settings.database_url,
    pool_size=database_settings.DB_POOL_SIZE,
    max_overflow=database_settings.DB_MAX_OVERFLOW,
    echo=database_settings.DB_ECHO,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields"""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


# Dependency to get database session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

                files["src/models/base.py"] = base_model_content

                # Generate example model
                example_model_content = '''"""
Example User Model
Auto-generated by Scaffolder Database Manager
"""

from sqlalchemy import Column, String

from .base import BaseModel


class User(BaseModel):
    """User model example"""

    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(String, default=True)
    is_superuser = Column(String, default=False)
'''

                files["src/models/user.py"] = example_model_content

            elif orm_type == ORMType.PYMONGO:
                # Generate PyMongo setup
                mongo_setup_content = '''"""
MongoDB Setup
Auto-generated by Scaffolder Database Manager
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

from ..config.database import database_settings


class MongoDB:
    """MongoDB connection manager"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(database_settings.database_url)
            self.database = self.client[database_settings.DB_NAME]
            # Test connection
            await self.client.admin.command('ping')
            print("Connected to MongoDB")
        except ConnectionFailure:
            print("Failed to connect to MongoDB")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_database(self):
        """Get database instance"""
        return self.database


# Global MongoDB instance
mongodb = MongoDB()
'''

                files["src/database/mongodb.py"] = mongo_setup_content

        elif language.lower() == "javascript" or language.lower() == "typescript":
            if orm_type == ORMType.PYMONGO:  # Using mongoose for Node.js
                # Generate Mongoose models
                user_model_content = """/**
 * User Model
 * Auto-generated by Scaffolder Database Manager
 */

import mongoose, {{ Schema, Document }} from 'mongoose';

export interface IUser extends Document {{
  email: string;
  username: string;
  password: string;
  fullName?: string;
  isActive: boolean;
  isSuperuser: boolean;
  createdAt: Date;
  updatedAt: Date;
}}

const UserSchema: Schema = new Schema({{
  email: {{
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true
  }},
  username: {{
    type: String,
    required: true,
    unique: true,
    trim: true
  }},
  password: {{
    type: String,
    required: true
  }},
  fullName: {{
    type: String,
    trim: true
  }},
  isActive: {{
    type: Boolean,
    default: true
  }},
  isSuperuser: {{
    type: Boolean,
    default: false
  }}
}}, {{
  timestamps: true
}});

// Index for better query performance
UserSchema.index({{ email: 1 }});
UserSchema.index({{ username: 1 }});

export default mongoose.model<IUser>('User', UserSchema);
"""

                files["src/models/User.ts"] = user_model_content

        return files

    async def _generate_migration_setup(
        self,
        project_path: Path,
        language: str,
        database_type: DatabaseType,
        migration_tool: MigrationTool,
    ) -> Dict[str, Any]:
        """Generate database migration setup"""

        files = {}

        if language.lower() == "python" and migration_tool == MigrationTool.ALEMBIC:
            # Generate Alembic configuration
            alembic_ini = """# Alembic configuration
# Auto-generated by Scaffolder Database Manager

[alembic]
script_location = src/database/migrations
sqlalchemy.url = %(DATABASE_URL)s

[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# after generating new revision scripts.

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

            files["alembic.ini"] = alembic_ini

            # Generate migration environment
            env_py = '''"""
Alembic Migration Environment
Auto-generated by Scaffolder Database Manager
"""

import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add src to path
sys.path.insert(0, 'src')

# Import database settings
from config.database import database_settings

# this is the Alembic Config object
config = context.config

# Set database URL
config.set_main_option("sqlalchemy.url", database_settings.database_url)

# Import all models
from models.base import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

            files["src/database/migrations/env.py"] = env_py

        elif (
            language.lower() == "javascript"
            and migration_tool == MigrationTool.MONGOOSE
        ):
            # Generate migration setup for Node.js/MongoDB
            migrate_config = """/**
 * Migration Configuration
 * Auto-generated by Scaffolder Database Manager
 */

require('dotenv').config();
const mongoose = require('mongoose');

const migrateConfig = {{
  uri: process.env.MONGODB_URI || 'mongodb://localhost:27017/mydatabase',
  collection: 'migrations',
  migrationsPath: './migrations',
  templatePath: './migration-template.js'
}};

module.exports = migrateConfig;
"""

            files["migrate-config.js"] = migrate_config

        return files

    async def _generate_database_utilities(
        self,
        project_path: Path,
        language: str,
        database_type: DatabaseType,
        features: List[DatabaseFeature],
    ) -> Dict[str, Any]:
        """Generate database utility functions"""

        files = {}

        if language.lower() == "python":
            utilities_content = '''"""
Database Utilities
Auto-generated by Scaffolder Database Manager
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..config.database import database_settings


class DatabaseUtils:
    """Database utility functions"""

    def __init__(self):
        self.engine = None
        self.async_session = None

    async def initialize(self):
        """Initialize database connection"""
        database_url = database_settings.database_url

        # Convert to async URL if needed
        if database_url.startswith('postgresql'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
        elif database_url.startswith('mysql'):
            database_url = database_url.replace('mysql://', 'mysql+aiomysql://')

        self.engine = create_async_engine(
            database_url,
            pool_size=database_settings.DB_POOL_SIZE,
            max_overflow=database_settings.DB_MAX_OVERFLOW,
            echo=database_settings.DB_ECHO,
        )

        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager"""
        if not self.async_session:
            await self.initialize()

        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def execute_query(self, query: str, params: Optional[dict] = None) -> List[dict]:
        """Execute raw SQL query"""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return [dict(row) for row in result.fetchall()]

    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False


# Global database utilities instance
db_utils = DatabaseUtils()


async def init_database():
    """Initialize database on startup"""
    await db_utils.initialize()


async def close_database():
    """Close database on shutdown"""
    await db_utils.close()
'''

            files["src/database/utils.py"] = utilities_content

            # Generate seed data script
            seed_content = '''"""
Database Seeding Script
Auto-generated by Scaffolder Database Manager
"""

import asyncio

from .utils import db_utils
from ..models.user import User


async def seed_database():
    """Seed database with initial data"""

    async with db_utils.get_session() as session:
        # Create admin user
        admin_user = User(
            email="admin@example.com",
            username="admin",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6fYzYXkqO",  # "password"
            full_name="Admin User",
            is_active=True,
            is_superuser=True
        )

        session.add(admin_user)
        await session.commit()

        print("Database seeded successfully")


if __name__ == "__main__":
    asyncio.run(seed_database())
'''

            files["scripts/seed_database.py"] = seed_content

        return files

    async def _generate_database_docker(
        self,
        project_path: Path,
        database_type: DatabaseType,
        config: DatabaseConfig,
    ) -> Dict[str, Any]:
        """Generate Docker setup for database"""

        files = {}

        # Generate docker-compose for database
        if database_type == DatabaseType.POSTGRESQL:
            docker_compose = f"""version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: {config.database}_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: {config.database}
      POSTGRES_USER: {config.username}
      POSTGRES_PASSWORD: {config.password}
    ports:
      - "{config.port}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app_network

volumes:
  postgres_data:

networks:
  app_network:
    driver: bridge
"""

        elif database_type == DatabaseType.MYSQL:
            docker_compose = f"""version: '3.8'

services:
  db:
    image: mysql:8.0
    container_name: {config.database}_db
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: {config.database}
      MYSQL_USER: {config.username}
      MYSQL_PASSWORD: {config.password}
      MYSQL_ROOT_PASSWORD: rootpassword
    ports:
      - "{config.port}:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app_network

volumes:
  mysql_data:

networks:
  app_network:
    driver: bridge
"""

        elif database_type == DatabaseType.MONGODB:
            docker_compose = f"""version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: {config.database}_mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_DATABASE: {config.database}
      MONGO_INITDB_ROOT_USERNAME: {config.username}
      MONGO_INITDB_ROOT_PASSWORD: {config.password}
    ports:
      - "{config.port}:27017"
    volumes:
      - mongodb_data:/data/db
      - ./scripts/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js
    networks:
      - app_network

volumes:
  mongodb_data:

networks:
  app_network:
    driver: bridge
"""

        elif database_type == DatabaseType.REDIS:
            docker_compose = f"""version: '3.8'

services:
  redis:
    image: redis:7.2-alpine
    container_name: {config.database}_redis
    restart: unless-stopped
    ports:
      - "{config.port}:6379"
    volumes:
      - redis_data:/data
    networks:
      - app_network

volumes:
  redis_data:

networks:
  app_network:
    driver: bridge
"""

        else:
            docker_compose = (
                "# Database Docker setup not available for this database type"
            )

        files["docker-compose.db.yml"] = docker_compose

        # Generate database initialization script
        init_sql = f"""-- Database Initialization Script
-- Auto-generated by Scaffolder Database Manager

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS {config.database};

-- Create user if it doesn't exist
CREATE USER IF NOT EXISTS '{config.username}'@'%' IDENTIFIED BY '{config.password}';

-- Grant privileges
GRANT ALL PRIVILEGES ON {config.database}.* TO '{config.username}'@'%';

-- Flush privileges
FLUSH PRIVILEGES;
"""

        files["scripts/init.sql"] = init_sql

        return files

    def _get_default_config(self, database_type: DatabaseType) -> DatabaseConfig:
        """Get default database configuration based on type"""

        if database_type == DatabaseType.POSTGRESQL:
            return DatabaseConfig(
                host="localhost",
                port=5432,
                database="myapp",
                username="myuser",
                password="mypassword",
                ssl_mode="prefer",
                connection_pool_size=10,
                connection_timeout=30,
            )
        elif database_type == DatabaseType.MYSQL:
            return DatabaseConfig(
                host="localhost",
                port=3306,
                database="myapp",
                username="myuser",
                password="mypassword",
                ssl_mode="prefer",
                connection_pool_size=10,
                connection_timeout=30,
            )
        elif database_type == DatabaseType.MONGODB:
            return DatabaseConfig(
                host="localhost",
                port=27017,
                database="myapp",
                username="myuser",
                password="mypassword",
                ssl_mode="prefer",
                connection_pool_size=10,
                connection_timeout=30,
            )
        elif database_type == DatabaseType.REDIS:
            return DatabaseConfig(
                host="localhost",
                port=6379,
                database="0",  # Redis database number
                username="",  # Redis usually doesn't use username
                password="",  # Set password if needed
                ssl_mode="prefer",
                connection_pool_size=10,
                connection_timeout=30,
            )
        else:  # SQLite
            return DatabaseConfig(
                host="",
                port=0,
                database="myapp.db",
                username="",
                password="",
                ssl_mode="prefer",
                connection_pool_size=1,
                connection_timeout=30,
            )
