from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import or_
from app.database import get_session
from app.models import Persona, Relacion, TipoRelacion
from app.schemas import PersonaCreate, PersonaRead, PersonaUpdate, ArbolResponse

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("/", response_model=list[PersonaRead])
def list_personas(session: Session = Depends(get_session)):
    return session.exec(select(Persona)).all()


@router.post("/", response_model=PersonaRead, status_code=201)
def create_persona(persona: PersonaCreate, session: Session = Depends(get_session)):
    db_persona = Persona(**persona.model_dump())
    session.add(db_persona)
    session.commit()
    session.refresh(db_persona)
    return db_persona


@router.get("/{persona_id}", response_model=PersonaRead)
def get_persona(persona_id: int, session: Session = Depends(get_session)):
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return persona


@router.put("/{persona_id}", response_model=PersonaRead)
def update_persona(persona_id: int, updates: PersonaUpdate, session: Session = Depends(get_session)):
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(persona, key, value)
    session.add(persona)
    session.commit()
    session.refresh(persona)
    return persona


@router.delete("/{persona_id}", status_code=204)
def delete_persona(persona_id: int, session: Session = Depends(get_session)):
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    session.delete(persona)
    session.commit()


@router.get("/{persona_id}/arbol", response_model=ArbolResponse)
def get_arbol(persona_id: int, session: Session = Depends(get_session)):
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    # Padres: persona_a es progenitor de persona_id
    padres_rels = session.exec(
        select(Relacion).where(
            Relacion.persona_b_id == persona_id,
            Relacion.tipo == TipoRelacion.progenitor
        )
    ).all()
    padres = [session.get(Persona, r.persona_a_id) for r in padres_rels]
    padre_ids = [p.id for p in padres if p]

    # Hijos: persona_id es progenitor de persona_b
    hijos_rels = session.exec(
        select(Relacion).where(
            Relacion.persona_a_id == persona_id,
            Relacion.tipo == TipoRelacion.progenitor
        )
    ).all()
    hijos = [session.get(Persona, r.persona_b_id) for r in hijos_rels]

    # Abuelos: progenitores de los padres
    abuelos = []
    abuelo_ids = set()
    for padre in padres:
        if not padre:
            continue
        abuelos_rels = session.exec(
            select(Relacion).where(
                Relacion.persona_b_id == padre.id,
                Relacion.tipo == TipoRelacion.progenitor
            )
        ).all()
        for r in abuelos_rels:
            if r.persona_a_id not in abuelo_ids:
                abuelo_ids.add(r.persona_a_id)
                ab = session.get(Persona, r.persona_a_id)
                if ab:
                    abuelos.append(ab)

    # Hermanos: comparten al menos un padre
    hermanos = []
    if padre_ids:
        hermanos_rels = session.exec(
            select(Relacion).where(
                Relacion.persona_a_id.in_(padre_ids),
                Relacion.tipo == TipoRelacion.progenitor,
                Relacion.persona_b_id != persona_id
            )
        ).all()
        hermano_ids = set()
        for r in hermanos_rels:
            if r.persona_b_id not in hermano_ids:
                hermano_ids.add(r.persona_b_id)
                h = session.get(Persona, r.persona_b_id)
                if h:
                    hermanos.append(h)

    # Parejas
    parejas_rels = session.exec(
        select(Relacion).where(
            or_(
                Relacion.persona_a_id == persona_id,
                Relacion.persona_b_id == persona_id
            ),
            Relacion.tipo == TipoRelacion.pareja
        )
    ).all()
    parejas = []
    for r in parejas_rels:
        pid = r.persona_b_id if r.persona_a_id == persona_id else r.persona_a_id
        p = session.get(Persona, pid)
        if p:
            parejas.append(p)

    return ArbolResponse(
        persona=persona,
        abuelos=[p for p in abuelos if p],
        padres=[p for p in padres if p],
        hermanos=hermanos,
        parejas=parejas,
        hijos=[p for p in hijos if p],
    )
