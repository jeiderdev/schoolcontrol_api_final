from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from database import Base
from sqlalchemy.orm import relationship

# ----------------------
# Materias
# ----------------------
class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(250))

    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    teacher = relationship("User", back_populates="subjects")
    enrollments = relationship("Enrollment", back_populates="subject")
    evaluations = relationship("Evaluation", back_populates="subject")