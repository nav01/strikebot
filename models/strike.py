import datetime
import enum

from .base import Base

from sqlalchemy import Table, Column, Integer, SmallInteger, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

import enum
from sqlalchemy import Integer, Enum

class Action(enum.Enum):
    add = 1
    remove = 2
    
class Strike(Base):
    __tablename__ = 'strike'
    
    id = Column(Integer, primary_key=True)
    decayed = Column(Boolean, default=False, nullable=False)
    server_id = Column(Integer, ForeignKey('server.id'), nullable=False)
    proposing_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    targeted_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    action = Column(Enum(Action), nullable=False)
    strike_level_modified = Column(SmallInteger, default=None)
    reason = Column(String(500), nullable=False)
    watched_message_id = Column(Integer)
    watched_message_channel_id = Column(Integer)
    watched_message_jump_url = Column(String(150))
    success = Column(Boolean, default=False, nullable=False)
    proposed_at = Column(DateTime, default=datetime.datetime.now, nullable=False)
    voting_ends_at = Column(DateTime)
    succeeded_at = Column(DateTime)
    
    server = relationship('Server')
    proposing_user = relationship('User', foreign_keys='Strike.proposing_user_id', back_populates='strikes_proposed')
    targeted_user = relationship('User', foreign_keys='Strike.targeted_user_id', back_populates='strikes_targeted_at')
    proponents = relationship('StrikeProponent', back_populates='strike')
    
    def decay(self):
        self.decayed = True