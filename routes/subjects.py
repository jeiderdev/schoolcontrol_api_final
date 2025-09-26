from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from models.subject import Subject
from models.user import User, UserRole
from routes.dtos import CreateSubjectDto, SubjectDto, UpdateSubjectDto
from .users import get_current_user  # Reutilizamos la función de autenticación


router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("/", response_model=list[SubjectDto])
def list_subjects(db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    if curr_user.role == UserRole.TEACHER:
        return db.query(Subject).filter(Subject.teacher_id == curr_user.id).all()
    if curr_user.role == UserRole.STUDENT:
        return db.query(Subject).join(Subject.enrollments).filter_by(student_id=curr_user.id).all()
    return db.query(Subject).all()


@router.post("/", response_model=SubjectDto)
def create_subject(
    subject_data: CreateSubjectDto,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    if curr_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permiso para crear asignaturas")

    new_subject = Subject(
        name=subject_data.name,
        description=subject_data.description,
        teacher_id=subject_data.teacher_id
    )
    try:
        db.add(new_subject)
        db.commit()
        db.refresh(new_subject)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear asignatura: {str(e)}")
    return new_subject


@router.get("/{subject_id}", response_model=SubjectDto)
def get_subject(subject_id: int, db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")
    if curr_user.role == UserRole.TEACHER and curr_user.id != subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver esta asignatura")
    if curr_user.role == UserRole.STUDENT:
        enrollment = db.query(Subject).join(Subject.enrollments).filter(
            Subject.id == subject_id,
            Subject.enrollments.any(student_id=curr_user.id)
        ).first()
        if not enrollment:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver esta asignatura")
    return subject


@router.put("/{subject_id}", response_model=SubjectDto)
def update_subject(
    subject_id: int,
    subject_data: UpdateSubjectDto,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")

    if curr_user.role != UserRole.ADMIN and curr_user.id != subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta asignatura")

    if subject_data.name is not None:
        subject.name = subject_data.name
    if subject_data.description is not None:
        subject.description = subject_data.description
    if subject_data.teacher_id is not None:
        subject.teacher_id = subject_data.teacher_id

    try:
        db.commit()
        db.refresh(subject)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar asignatura: {str(e)}")
    return subject


@router.delete("/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")

    if curr_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar asignaturas")

    try:
        db.delete(subject)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar asignatura: {str(e)}")
    return {"message": "Asignatura eliminada correctamente"}
