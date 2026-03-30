import httpx
import json
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, Session, select

from app.database import get_session
from app.models import Persona, Relacion, TipoRelacion

router = APIRouter(tags=["interpretar"])

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


@router.post("/interpretar")
async def interpretar(body: InterpretarRequest, session: Session = Depends(get_session)):
    texto = body.texto.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Texto vacío")

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            res = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": PROMPT.format(texto=texto),
                    "stream": False,
                    "format": "json",
                },
            )
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Ollama no está disponible")

    try:
        extracted = json.loads(res.json()["response"])
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=500, detail="El modelo no devolvió JSON válido")

    existentes = session.exec(select(Persona)).all()

    indice_a_id: dict[int, int] = {}
    personas_creadas: list[str] = []

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
             and e.primer_apellido.lower() == primer_ap.lower()),
            None,
        )

        if match:
            indice_a_id[indice] = match.id
        else:
            nueva = Persona(nombre=nombre, primer_apellido=primer_ap, segundo_apellido=segundo_ap)
            session.add(nueva)
            session.flush()
            indice_a_id[indice] = nueva.id
            personas_creadas.append(f"{nombre} {primer_ap}")

    relaciones_creadas = 0
    for r in extracted.get("relaciones", []):
        a_idx = r.get("persona_a")
        b_idx = r.get("persona_b")
        tipo_str = r.get("tipo", "")

        if a_idx not in indice_a_id or b_idx not in indice_a_id:
            continue
        try:
            tipo = TipoRelacion(tipo_str)
        except ValueError:
            continue

        session.add(Relacion(
            persona_a_id=indice_a_id[a_idx],
            persona_b_id=indice_a_id[b_idx],
            tipo=tipo,
        ))
        relaciones_creadas += 1

    session.commit()

    return {
        "personas_creadas": personas_creadas,
        "relaciones_creadas": relaciones_creadas,
    }
