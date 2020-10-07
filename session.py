from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models import server, user, strike, strike_proponent

engine = create_engine('sqlite:///:memory:', echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)