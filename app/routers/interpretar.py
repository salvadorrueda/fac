import httpx
import json
import logging
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, Session, select
from typing import Optional

from app.database import get_session
from app.models import Persona, Relacion, TipoRelacion

router = APIRouter(tags=["interpretar"])
log = logging.getLogger("fac.interpretar")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

PROMPT = """\
Eres un asistente que extrae personas y relaciones de texto en español.

Tipos de relación válidos: progenitor, pareja, amigo, conocido.
Para "progenitor": persona_a es el padre o la madre, persona_b es el hijo o la hija.

Devuelve SOLO un objeto JSON con este formato exacto:
{{
  "personas": [
    {{"indice": 0, "nombre": "...", "primer_apellido": "...", "segundo_apellido": "..."}}
  ],
  "relaciones": [
    {{"persona_a": 0, "persona_b": 1, "tipo": "progenitor"}}
  ]
}}

Usa null si no hay segundo apellido. Si no hay relaciones claras, devuelve listas vacías.

Texto: "{texto}"
"""


class InterpretarRequest(SQLModel):
    texto: str


class PersonaPreview(SQLModel):
    indice: int
    nombre: str
    primer_apellido: str
    segundo_apellido: Optional[str] = None
    es_nueva: bool
    id: Optional[int] = None   # None si es nueva


class RelacionPreview(SQLModel):
    persona_a: int   # indice en la lista de personas
    persona_b: int
    tipo: str


class Preview(SQLModel):
    personas: list[PersonaPreview]
    relaciones: list[RelacionPreview]


class ConfirmarRequest(SQLModel):
    preview: Preview


@router.post("/interpretar", response_model=Preview)
async def interpretar(body: InterpretarRequest, session: Session = Depends(get_session)):
    texto = body.texto.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Texto vacío")

    prompt = PROMPT.format(texto=texto)
    log.info("─── Ollama request ───────────────────────────")
    log.info("Model : %s", OLLAMA_MODEL)
    log.info("Prompt:\n%s", prompt)

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            res = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
        except httpx.ConnectError:
            log.error("Ollama no está disponible en %s", OLLAMA_URL)
            raise HTTPException(status_code=503, detail="Ollama no está disponible")

    raw_response = res.json().get("response", "")
    log.info("─── Ollama response ──────────────────────────")
    log.info("Raw JSON: %s", raw_response)

    try:
        extracted = json.loads(raw_response)
        log.info("Parsed  : %s", json.dumps(extracted, ensure_ascii=False, indent=2))
    except (json.JSONDecodeError, KeyError):
        log.error("JSON inválido recibido de Ollama: %s", raw_response)
        raise HTTPException(status_code=500, detail="El modelo no devolvió JSON válido")

    existentes = session.exec(select(Persona)).all()

    personas_preview: list[PersonaPreview] = []
    for p in extracted.get("personas", []):
        indice = p.get("indice")
        nombre = (p.get("nombre") or "").strip()
        primer_ap = (p.get("primer_apellido") or "").strip()
        segundo_ap = p.get("segundo_apellido") or None

        if not nombre or not primer_ap:
            continue

        match = next(
            (e for e in existentes
             if e.nombre.lower() == nombre.lower()
             and e.primer_apellido.lower() == primer_ap.lower()
             and (e.segundo_apellido or "").lower() == (segundo_ap or "").lower()),
            None,
        )

        personas_preview.append(PersonaPreview(
            indice=indice,
            nombre=nombre,
            primer_apellido=primer_ap,
            segundo_apellido=segundo_ap,
            es_nueva=match is None,
            id=match.id if match else None,
        ))

    relaciones_preview: list[RelacionPreview] = []
    indices_validos = {p.indice for p in personas_preview}
    for r in extracted.get("relaciones", []):
        a_idx = r.get("persona_a")
        b_idx = r.get("persona_b")
        tipo_str = r.get("tipo", "")
        if a_idx not in indices_validos or b_idx not in indices_validos:
            continue
        try:
            TipoRelacion(tipo_str)
        except ValueError:
            continue
        relaciones_preview.append(RelacionPreview(
            persona_a=a_idx,
            persona_b=b_idx,
            tipo=tipo_str,
        ))

    return Preview(personas=personas_preview, relaciones=relaciones_preview)


@router.post("/interpretar/confirmar")
def confirmar(body: ConfirmarRequest, session: Session = Depends(get_session)):
    preview = body.preview
    indice_a_id: dict[int, int] = {}
    personas_creadas: list[str] = []

    for p in preview.personas:
        if p.es_nueva:
            nueva = Persona(
                nombre=p.nombre,
                primer_apellido=p.primer_apellido,
                segundo_apellido=p.segundo_apellido,
            )
            session.add(nueva)
            session.flush()
            indice_a_id[p.indice] = nueva.id
            personas_creadas.append(f"{p.nombre} {p.primer_apellido}")
        else:
            indice_a_id[p.indice] = p.id

    relaciones_creadas = 0
    for r in preview.relaciones:
        if r.persona_a not in indice_a_id or r.persona_b not in indice_a_id:
            continue
        session.add(Relacion(
            persona_a_id=indice_a_id[r.persona_a],
            persona_b_id=indice_a_id[r.persona_b],
            tipo=TipoRelacion(r.tipo),
        ))
        relaciones_creadas += 1

    session.commit()
    return {"personas_creadas": personas_creadas, "relaciones_creadas": relaciones_creadas}
