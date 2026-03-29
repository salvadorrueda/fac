from sqlmodel import SQLModel
from typing import Optional
from app.models import TipoRelacion


class PersonaCreate(SQLModel):
    nombre: str
    primer_apellido: str
    segundo_apellido: Optional[str] = None
    apodo: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    fecha_defuncion: Optional[str] = None
    notas: Optional[str] = None


class PersonaRead(PersonaCreate):
    id: int


class PersonaUpdate(SQLModel):
    nombre: Optional[str] = None
    primer_apellido: Optional[str] = None
    segundo_apellido: Optional[str] = None
    apodo: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    fecha_defuncion: Optional[str] = None
    notas: Optional[str] = None


class RelacionCreate(SQLModel):
    persona_a_id: int
    persona_b_id: int
    tipo: TipoRelacion
    comentario: Optional[str] = None


class RelacionRead(RelacionCreate):
    id: int


class RelacionUpdate(SQLModel):
    tipo: Optional[TipoRelacion] = None
    comentario: Optional[str] = None


class ArbolResponse(SQLModel):
    persona: PersonaRead
    abuelos: list[PersonaRead]
    padres: list[PersonaRead]
    hermanos: list[PersonaRead]
    parejas: list[PersonaRead]
    hijos: list[PersonaRead]
