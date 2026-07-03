from sqlalchemy import Column, Integer, String, Text
from database.database import Base


class ChatMessageDB(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    role = Column(String)  # user / assistant
    content = Column(Text)