from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.grade import Grade
from models.evaluation import Evaluation
from models.subject import Subject
from models.user import User, UserRole
from typing import List

from routes.dtos import CreateGradeDto, GradeDto, UpdateGradeDto
from .users import get_current_user  # autenticación


router = APIRouter(prefix="/grades", tags=["grades"])

# --- Endpoints --- #

@router.get("/", response_model=List[GradeDto])
def list_grades(
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    if curr_user.role == UserRole.STUDENT:
        # Un estudiante solo puede ver sus notas
        return db.query(Grade).filter(Grade.student_id == curr_user.id).all()
    if curr_user.role == UserRole.TEACHER:
        # Un profesor solo puede ver las notas de sus materias
        return db.query(Grade).join(Grade.evaluation).join(Evaluation.subject).filter(
            Subject.teacher_id == curr_user.id
        ).all()
    return db.query(Grade).all()


@router.post("/", response_model=GradeDto)
def create_grade(
    grade_data: CreateGradeDto,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == grade_data.evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    subject = db.query(Subject).filter(Subject.id == evaluation.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Solo admin o profesor dueño de la materia
    if curr_user.role != UserRole.ADMIN and curr_user.id != subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para asignar notas en esta materia")

    grade = Grade(
        student_id=grade_data.student_id,
        evaluation_id=grade_data.evaluation_id,
        score=grade_data.score
    )

    try:
        db.add(grade)
        db.commit()
        db.refresh(grade)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear nota: {str(e)}")

    return grade

@router.get("/evaluation/{evaluation_id}", response_model=List[GradeDto])
def list_grades_by_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    subject = db.query(Subject).filter(Subject.id == evaluation.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Permisos: solo admin, profesor dueño de la materia o estudiantes matriculados
    if curr_user.role != UserRole.ADMIN and curr_user.id != subject.teacher_id:
        if curr_user.role == UserRole.STUDENT:
            enrollment = db.query(Subject).join(Subject.enrollments).filter(
                Subject.id == subject.id,
                Subject.enrollments.any(student_id=curr_user.id)
            ).first()
            if not enrollment:
                raise HTTPException(status_code=403, detail="No tienes permiso para ver estas notas")
            return db.query(Grade).filter(
                Grade.evaluation_id == evaluation_id,
                Grade.student_id == curr_user.id
            ).all()
        else:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver estas notas")

    return db.query(Grade).filter(Grade.evaluation_id == evaluation_id).all()

@router.get("/subject/{subject_id}", response_model=List[GradeDto])
def list_grades_by_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Permisos: solo admin, profesor dueño de la materia o estudiantes matriculados
    if curr_user.role != UserRole.ADMIN and curr_user.id != subject.teacher_id:
        if curr_user.role == UserRole.STUDENT:
            enrollment = db.query(Subject).join(Subject.enrollments).filter(
                Subject.id == subject_id,
                Subject.enrollments.any(student_id=curr_user.id)
            ).first()
            if not enrollment:
                raise HTTPException(status_code=403, detail="No tienes permiso para ver estas notas")
            return db.query(Grade).join(Grade.evaluation).filter(
                Evaluation.subject_id == subject_id,
                Grade.student_id == curr_user.id
            ).all()
        else:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver estas notas")

    return db.query(Grade).join(Grade.evaluation).filter(Evaluation.subject_id == subject_id).all()

@router.get("/{grade_id}", response_model=GradeDto)
def get_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Nota no encontrada")

    if curr_user.role == UserRole.STUDENT and grade.student_id != curr_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver esta nota")

    return grade


@router.put("/{grade_id}", response_model=GradeDto)
def update_grade(
    grade_id: int,
    grade_data: UpdateGradeDto,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Nota no encontrada")

    subject = db.query(Subject).filter(Subject.id == grade.evaluation.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Solo admin o profesor dueño de la materia
    if curr_user.role != UserRole.ADMIN and curr_user.id != subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar esta nota")

    if grade_data.score is not None:
        grade.score = grade_data.score

    try:
        db.commit()
        db.refresh(grade)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar nota: {str(e)}")

    return grade


@router.delete("/{grade_id}", response_model=dict)
def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Nota no encontrada")

    subject = db.query(Subject).filter(Subject.id == grade.evaluation.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Solo admin o profesor dueño de la materia
    if curr_user.role != UserRole.ADMIN and curr_user.id != subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta nota")

    try:
        db.delete(grade)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar nota: {str(e)}")

    return {"message": "Nota eliminada correctamente"}
