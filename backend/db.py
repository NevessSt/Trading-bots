"""Shared database instance for all models."""
from flask_sqlalchemy import SQLAlchemy

# Shared database instance
db = SQLAlchemy()