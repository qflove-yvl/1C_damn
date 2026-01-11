from sqlalchemy import Column, Integer, String
from backend.database import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    client_name = Column(String)
    client_username = Column(String)
    client_chat_id = Column(String)
    text = Column(String)
    status = Column(String, default="Новый")

    created_at = Column(DateTime, default=datetime.utcnow)



class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
