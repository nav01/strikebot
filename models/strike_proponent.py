from .base import Base

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class StrikeProponent(Base):
    __tablename__ = 'strike_proponent'
    
    id = Column(Integer, primary_key=True)
    strike_id = Column(Integer, ForeignKey('strike.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    strike = relationship('Strike', back_populates='proponents')
    user = relationship('User')