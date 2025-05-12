# Setting up our SQLAlchemy 
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, declarative_base
import dotenv
import os

# Set your DB Url 
# This will set a llm.db inside of our current directory 
PROD = True
DATABASE_URI = ''

if PROD:
    dotenv.load_dotenv()
    # Production url 
    DATABASE_URI = os.getenv('DATABASE_URI')
else:
    # Local URL
    DATABASE_URI = 'sqlite:///./llm.db'

# Creating the session for our routers to import 
# Because we're on a free service from Render.com, we need to work with connection pooling
# 
# We're basically saying: Keep 7 connections opened, if there are more than 7 we'll allow 3 more and keep 30 seconds for a timer to search for an open spot
engine = create_engine(DATABASE_URI, pool_size=7, max_overflow=3, pool_timeout=30)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base to create a model 
Base = declarative_base()