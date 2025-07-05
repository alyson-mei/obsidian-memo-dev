"""
models.py

Defines all SQLAlchemy ORM models for the application's database tables, including Commit, Weather,
Time, Geo, Bing, and Journal. Each model specifies its table name, columns, and types, and includes
a timestamp column that is automatically updated on modification.

Key features:
- Declarative model definitions for all major data entities.
- Consistent use of primary keys, autoincrement, and indexing.
- Timestamp columns for tracking updates.
- Designed for use with async SQLAlchemy sessions.

Dependencies:
- SQLAlchemy (Column, Integer, DateTime, Text, func)
- app.data.database (for declarative Base)
"""

from sqlalchemy import Column, Integer, DateTime, Text
from sqlalchemy.sql import func

from app.data.database import Base

class Commit(Base):
    __tablename__ = "commit"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), onupdate=func.now())
    
class Weather(Base):
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), onupdate=func.now())

class Time(Base):
    __tablename__ = "time"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    message_light = Column(Text, nullable=False)
    message_dark = Column(Text, nullable=False)
    date = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), onupdate=func.now())

class Geo(Base):
    __tablename__ = "geo"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    place = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    urls = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), onupdate=func.now())

class Bing(Base):
    __tablename__ = "bing"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    url = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    page_date = Column(Text, nullable=True)
    copyright = Column(Text, nullable=True)
    page_url = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), onupdate=func.now())

class Journal(Base):
    __tablename__ = "journal"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    event = Column(Text, nullable=False)
    journal = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), onupdate=func.now())
