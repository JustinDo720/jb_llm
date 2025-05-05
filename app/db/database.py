# Setting up our SQLAlchemy 
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, declarative_base

# Set your DB Url 
# This will set a llm.db inside of our current directory 
DATABASE_URI = 'sqlite:///./llm.db'

# Creating the session for our routers to import 
engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base to create a model 
Base = declarative_base()