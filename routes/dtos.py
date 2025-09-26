from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from models.user import UserRole
from datetime import datetime

class CreateUserDto(BaseModel):
    name: str
    idnumber: str
    email: EmailStr
    age: int
    role: UserRole
    password: str
    photo: str | None = None
    active: bool = True

class UpdateUserDto(BaseModel):
    name: str = None
    age: int = None
    password: str = None
    photo: str = None
    active: bool = None

class UserBaseDto(BaseModel):
    id: int
    name: str
    idnumber: str
    email: EmailStr
    age: int
    role: UserRole
    photo: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SubjectBaseDto(BaseModel):
    id: int
    name: str
    description: str | None
    teacher_id: int | None
    created_at: datetime
    updated_at: datetime

class EnrollmentBaseDto(BaseModel):
    id: int
    student_id: int
    subject_id: int
    active: bool
    enrolled_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True   
        
class GradeBaseDto(BaseModel):
    id: int
    student_id: int
    evaluation_id: int
    score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EvaluationBaseDto(BaseModel):
    id: int
    name: str
    subject_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserDto(UserBaseDto):
    # relaciones
    subjects: list[SubjectBaseDto] = []
    enrollments: list[EnrollmentBaseDto] = []
    grades: list[GradeBaseDto] = []

class TokenDto(BaseModel):
    access_token: str
    token_type: str
    user: UserDto  

class LoginDto(BaseModel):
    username: str
    password: str
    
class CreateSubjectDto(BaseModel):
    name: str
    description: str | None = None
    teacher_id: int | None = None


class UpdateSubjectDto(BaseModel):
    name: str | None = None
    description: str | None = None
    teacher_id: int | None = None

    class Config:
        from_attributes = True
        
class EvaluationDto(EvaluationBaseDto):
    # Relaciones
    subject: SubjectBaseDto
    grades: list[GradeBaseDto] = []

class SubjectDto(SubjectBaseDto):
    # Relaciones
    teacher: UserBaseDto
    enrollments: list[EnrollmentBaseDto] = []
    evaluations: list[EvaluationDto] = []
    
class CreateGradeDto(BaseModel):
    student_id: int
    evaluation_id: int
    score: float = Field(..., ge=0.0, le=5.0)


class UpdateGradeDto(BaseModel):
    score: Optional[float] = Field(None, ge=0.0, le=5.0)

class GradeDto(GradeBaseDto):
    # Relaciones
    student: UserBaseDto
    evaluation: EvaluationBaseDto
    
class CreateEvaluationDto(BaseModel):
    name: str
    subject_id: int


class UpdateEvaluationDto(BaseModel):
    name: Optional[str] = None
    

class CreateEnrollmentDto(BaseModel):
    student_id: int
    subject_id: int


class UpdateEnrollmentDto(BaseModel):
    active: Optional[bool] = None
        
class EnrollmentDto(EnrollmentBaseDto):
    # Relaciones
    student: UserBaseDto
    subject: SubjectBaseDto