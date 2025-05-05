from .database import Base
from sqlalchemy import Column, Integer, String 

class PremUserInfo(Base):
    # In FastAPI we need to make sure we have a table name 
    __tablename__ = 'user_info'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_title = Column(String)
    yrs_exp = Column(Integer)
    headline = Column(String)