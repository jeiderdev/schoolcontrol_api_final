from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, func
from sqlalchemy.orm import relationship
import enum
from database import Base

# ----------------------
# Enumeraciones
# ----------------------
class UserRole(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

# ----------------------
# Usuarios
# ----------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    idnumber = Column(String(15), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    age = Column(Integer, nullable=True)
    photo = Column(Text, nullable=True)  # URL o path a la foto
    active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Un profesor puede tener varias materias
    subjects = relationship("Subject", back_populates="teacher")
    # Un estudiante puede tener varias matrículas
    enrollments = relationship("Enrollment", back_populates="student")
    grades = relationship("Grade", back_populates="student")