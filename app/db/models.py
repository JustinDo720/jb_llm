from .database import Base
from sqlalchemy import Column, Integer, String, Text

class JobInterviewQuestion(Base):
    __tablename__ = 'job_interview_question'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    questions = Column(String)