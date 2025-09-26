from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from database import Base

# ----------------------
# Evaluaciones
# ----------------------
class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    percentage = Column(Integer, nullable=False, default=0)  # porcentaje de la evaluación en la materia
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relaciones
    subject = relationship("Subject", back_populates="evaluations")
    grades = relationship("Grade", back_populates="evaluation")