from .base import Base

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    discord_user_id = Column(Integer, unique=True, nullable=False)
    
    strikes_proposed = relationship('Strike', foreign_keys='Strike.proposing_user_id', back_populates='proposing_user')
    strikes_targeted_at = relationship('Strike', foreign_keys='Strike.targeted_user_id', back_populates='targeted_user')