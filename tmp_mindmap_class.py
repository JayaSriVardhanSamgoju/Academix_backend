
class MindMap(Base):
    __tablename__ = "mindmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, index=True)
    data = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="mindmaps")
