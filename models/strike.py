import datetime

from .base import Base

from sqlalchemy import Table, Column, Integer, SmallInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class Strike(Base):
    __tablename__ = 'strike'
    
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('server.id'), nullable=False)
    proposing_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    targeted_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    reason = Column(String(500), nullable=False)
    success = Column(Boolean, default=False, nullable=False)
    strike_level_applied = Column(SmallInteger, default=None)
    proposed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    server = relationship('server')
    proposing_user = relationship('user', foreign_keys='strike.proposing_user_id', back_populates='strikes_proposed')
    targeted_user = relationship('user', foreign_keys='strike.targeted_user_id', back_populates='strikes_targeted_at')
    proponents = relationship('strikeProponent', back_populates='strike')