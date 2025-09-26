from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, func
from database import Base
from sqlalchemy.orm import relationship

# ----------------------
# Matriculas (entidad)
# ----------------------


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)

    active = Column(Boolean, default=True)
    enrolled_at = Column(DateTime, server_default=func.now())
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relaciones
    student = relationship("User", back_populates="enrollments")
    subject = relationship("Subject", back_populates="enrollments")