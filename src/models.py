from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String, nullable=False)
    mac_address = Column(String, nullable=False)
    last_seen = Column(DateTime, nullable=False)

engine = create_engine('sqlite:///devices.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
