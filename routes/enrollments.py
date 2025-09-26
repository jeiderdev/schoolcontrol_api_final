from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.enrollment import Enrollment
from models.subject import Subject
from models.user import User, UserRole
from typing import  List

from routes.dtos import CreateEnrollmentDto, EnrollmentDto, UpdateEnrollmentDto

from .users import get_current_user  # reutilizamos la autenticación


router = APIRouter(prefix="/enrollments", tags=["enrollments"])

# --- Endpoints --- #

@router.get("/", response_model=List[EnrollmentDto])
def list_enrollments(
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    # Solo admin puede ver todas
    if curr_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver todas las matrículas")

    return db.query(Enrollment).all()


@router.get("/me", response_model=List[EnrollmentDto])
def list_my_enrollments(
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    # Solo estudiantes
    if curr_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Solo los estudiantes pueden ver sus matrículas")

    return db.query(Enrollment).filter(Enrollment.student_id == curr_user.id).all()


@router.post("/", response_model=EnrollmentDto)
def create_enrollment(
    enrollment_data: CreateEnrollmentDto,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    subject = db.query(Subject).filter(Subject.id == enrollment_data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Permisos: admin o profesor dueño de la materia
    if curr_user.role != UserRole.ADMIN and curr_user.id != subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para matricular en esta materia")

    # Evitar duplicados
    existing = db.query(Enrollment).filter(
        Enrollment.student_id == enrollment_data.student_id,
        Enrollment.subject_id == enrollment_data.subject_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="El estudiante ya está matriculado en esta materia")

    enrollment = Enrollment(
        student_id=enrollment_data.student_id,
        subject_id=enrollment_data.subject_id,
        active=True
    )
    try:
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear matrícula: {str(e)}")

    return enrollment


@router.put("/{enrollment_id}", response_model=EnrollmentDto)
def update_enrollment(
    enrollment_id: int,
    enrollment_data: UpdateEnrollmentDto,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")

    # Permisos: admin o profesor dueño de la materia
    if curr_user.role != UserRole.ADMIN and curr_user.id != enrollment.subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar esta matrícula")

    if enrollment_data.active is not None:
        enrollment.active = enrollment_data.active

    try:
        db.commit()
        db.refresh(enrollment)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar matrícula: {str(e)}")

    return enrollment


@router.delete("/{enrollment_id}", response_model=dict)
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")

    # Permisos: admin o profesor dueño de la materia
    if curr_user.role != UserRole.ADMIN and curr_user.id != enrollment.subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta matrícula")

    try:
        db.delete(enrollment)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar matrícula: {str(e)}")

    return {"message": "Matrícula eliminada correctamente"}
