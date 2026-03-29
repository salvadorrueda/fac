from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Relacion, Persona
from app.schemas import RelacionCreate, RelacionRead, RelacionUpdate

router = APIRouter(prefix="/relaciones", tags=["relaciones"])


@router.get("/", response_model=list[RelacionRead])
def list_relaciones(session: Session = Depends(get_session)):
    return session.exec(select(Relacion)).all()


@router.post("/", response_model=RelacionRead, status_code=201)
def create_relacion(relacion: RelacionCreate, session: Session = Depends(get_session)):
    for pid in [relacion.persona_a_id, relacion.persona_b_id]:
        if not session.get(Persona, pid):
            raise HTTPException(status_code=404, detail=f"Persona {pid} no encontrada")
    db_relacion = Relacion(**relacion.model_dump())
    session.add(db_relacion)
    session.commit()
    session.refresh(db_relacion)
    return db_relacion


@router.get("/{relacion_id}", response_model=RelacionRead)
def get_relacion(relacion_id: int, session: Session = Depends(get_session)):
    relacion = session.get(Relacion, relacion_id)
    if not relacion:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return relacion


@router.put("/{relacion_id}", response_model=RelacionRead)
def update_relacion(relacion_id: int, updates: RelacionUpdate, session: Session = Depends(get_session)):
    relacion = session.get(Relacion, relacion_id)
    if not relacion:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(relacion, key, value)
    session.add(relacion)
    session.commit()
    session.refresh(relacion)
    return relacion


@router.delete("/{relacion_id}", status_code=204)
def delete_relacion(relacion_id: int, session: Session = Depends(get_session)):
    relacion = session.get(Relacion, relacion_id)
    if not relacion:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    session.delete(relacion)
    session.commit()
