from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.evaluation import Evaluation
from models.subject import Subject
from models.user import User, UserRole
from typing import List

from routes.dtos import CreateEvaluationDto, EvaluationDto, UpdateEvaluationDto

from .users import get_current_user  # para autenticar

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


# --- Endpoints --- #
@router.get("/", response_model=List[EvaluationDto])
def list_evaluations(
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    return db.query(Evaluation).all()


@router.post("/", response_model=EvaluationDto)
def create_evaluation(
    evaluation_data: CreateEvaluationDto,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    # Solo Admins o el profesor dueño de la materia pueden crear evaluaciones
    subject = db.query(Subject).filter(Subject.id == evaluation_data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    if curr_user.role != UserRole.ADMIN and curr_user.id != subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para crear evaluaciones en esta materia")

    evaluation = Evaluation(
        name=evaluation_data.name,
        subject_id=evaluation_data.subject_id,
    )
    try:
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear evaluación: {str(e)}")

    return evaluation


@router.get("/{evaluation_id}", response_model=EvaluationDto)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    return evaluation


@router.put("/{evaluation_id}", response_model=EvaluationDto)
def update_evaluation(
    evaluation_id: int,
    evaluation_data: UpdateEvaluationDto,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    # Permisos: solo admin o profesor dueño de la materia
    if curr_user.role != UserRole.ADMIN and curr_user.id != evaluation.subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar esta evaluación")

    if evaluation_data.name is not None:
        evaluation.name = evaluation_data.name

    try:
        db.commit()
        db.refresh(evaluation)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar evaluación: {str(e)}")

    return evaluation


@router.delete("/{evaluation_id}", response_model=dict)
def delete_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    curr_user: User = Depends(get_current_user)
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    # Permisos: solo admin o profesor dueño de la materia
    if curr_user.role != UserRole.ADMIN and curr_user.id != evaluation.subject.teacher_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta evaluación")

    try:
        db.delete(evaluation)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar evaluación: {str(e)}")

    return {"message": "Evaluación eliminada correctamente"}
