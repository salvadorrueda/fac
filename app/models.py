from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum


class TipoRelacion(str, Enum):
    progenitor = "progenitor"
    pareja = "pareja"
    amigo = "amigo"
    conocido = "conocido"


class Persona(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    primer_apellido: str
    segundo_apellido: Optional[str] = None
    apodo: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    fecha_defuncion: Optional[str] = None
    notas: Optional[str] = None


class Relacion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    persona_a_id: int = Field(foreign_key="persona.id")
    persona_b_id: int = Field(foreign_key="persona.id")
    tipo: TipoRelacion
    comentario: Optional[str] = None
