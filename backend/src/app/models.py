import os

from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String, nullable=False)
    mac_address = Column(String, nullable=False)
    hostname = Column(String, nullable=False)
    last_seen = Column(DateTime, nullable=False)

sqlite_db = os.environ.get("SQLITE_DB")
if sqlite_db is None:
    raise Exception("SQLITE_DB environment variable not set")

engine = create_engine(f"sqlite:///{sqlite_db}")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
