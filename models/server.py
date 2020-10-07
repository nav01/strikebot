from .base import Base

from sqlalchemy import Table, Column, Integer
from sqlalchemy.orm import relationship

class Server(Base):
    __tablename__ = 'server'
    
    id = Column(Integer, primary_key=True)
    discord_server_id = Column(Integer, unique=True, nullable=False)
    
    strikes = relationship('strike')