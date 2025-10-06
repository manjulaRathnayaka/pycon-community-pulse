#!/usr/bin/env python3
"""Test database connection with Choreo-injected env vars"""
import os
import sys

print("=== Database Environment Variables ===")
print(f"DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")
print(f"DB_PORT: {os.getenv('DB_PORT', 'NOT SET')}")
print(f"DB_USER: {os.getenv('DB_USER', 'NOT SET')}")
print(f"DB_PASSWORD: {'***' if os.getenv('DB_PASSWORD') else 'NOT SET'}")
print(f"DB_NAME: {os.getenv('DB_NAME', 'NOT SET')}")
print()

# Import after printing env vars
from shared.config import config
print(f"Constructed DATABASE_URL: {config.DATABASE_URL[:50]}...")
print()

# Try connecting
from shared import get_db_context, Post

try:
    with get_db_context() as db:
        count = db.query(Post).count()
        print(f"✅ Database connection successful!")
        print(f"Total posts in database: {count}")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)
