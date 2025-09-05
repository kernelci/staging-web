# Copyright (C) 2025 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from models import Base, User, UserRole, Settings
from config import (
    DATABASE_URL,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_EMAIL,
    SETTINGS_KEYS,
)

SQLALCHEMY_DATABASE_URL = DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run_migrations():
    """Run database migrations to add any missing columns"""
    print("Checking for database migrations...")

    migrations = [
        {
            "table": "staging_run_steps",
            "column": "info_message",
            "type": "TEXT",
            "description": "Column for informational messages (warnings, skip reasons, etc.)",
        }
        # Add future migrations here
    ]

    with engine.connect() as conn:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        for migration in migrations:
            table_name = migration["table"]
            column_name = migration["column"]
            column_type = migration["type"]
            description = migration["description"]

            if table_name in table_names:
                columns = [col["name"] for col in inspector.get_columns(table_name)]

                if column_name not in columns:
                    print(f"Adding {column_name} column to {table_name}...")
                    print(f"  Description: {description}")
                    try:
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"✓ Successfully added {column_name} column")
                    except Exception as e:
                        print(f"✗ Error adding {column_name} column: {e}")
                else:
                    print(f"✓ {column_name} column already exists in {table_name}")
            else:
                print(f"✓ {table_name} table will be created by SQLAlchemy")

    print("Database migration check completed")


def init_db():
    """Initialize database and create default admin user"""
    # i know its ugly, but we can fix it later (TODO)
    from auth import get_password_hash  # Import here to avoid circular import

    Base.metadata.create_all(bind=engine)

    # Run migrations after creating tables
    run_migrations()

    # Create default admin user if not exists
    db = SessionLocal()
    try:
        admin_user = (
            db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        )
        if not admin_user:
            admin_user = User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=get_password_hash(DEFAULT_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                email=DEFAULT_ADMIN_EMAIL,
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created")

        # Create default settings
        for setting_name, setting_key in SETTINGS_KEYS.items():
            setting = db.query(Settings).filter(Settings.key == setting_key).first()
            if not setting:
                setting = Settings(key=setting_key, value="")
                db.add(setting)

        db.commit()

    finally:
        db.close()
