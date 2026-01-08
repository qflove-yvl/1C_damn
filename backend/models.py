from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    client_name = Column(String)
    client_username = Column(String)
    client_chat_id = Column(String)

    text = Column(String)
    status = Column(String, default="Новый")