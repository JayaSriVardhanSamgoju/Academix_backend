
class MindMap(Base):
    __tablename__ = "mindmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, index=True)
    data = Column(JSON) # Stores the hierarchical JSON structure
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="mindmaps")
