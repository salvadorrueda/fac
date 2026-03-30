## Diseño conceptual de *fac*

---

### Entidades principales

**Persona** — el núcleo del sistema
Atributos: nombre, apellidos, apodo, fecha de nacimiento, notas, foto.
La información de contacto (teléfono, email, dirección) la separo deliberadamente — ver abajo.

---

### Relaciones de Persona

#### 1. Persona ↔ Contacto (1:N)
Una persona puede tener varios datos de contacto: teléfono, email, red social, dirección...
Separarlo permite múltiples teléfonos, indicar cuál es preferido, y anotar el tipo (personal, trabajo, etc.).

#### 2. Persona ↔ Persona — **Relación** (N:M reflexiva)
Esta es la relación más importante. Une dos personas e indica cómo se conocen.

La clave de diseño aquí es si la relación es **simétrica o asimétrica**:
- *Amigo* es simétrica: si A es amigo de B, B es amigo de A.
- *Padre/hijo* es asimétrica: el rol de cada uno es distinto.

Una opción es guardar **dos roles**, uno por cada extremo:
`persona_a` → rol_a: *padre*, `persona_b` → rol_b: *hijo*

O simplemente guardar un único tipo de relación y deducir el inverso.

Atributos de la relación: tipo (familiar / amigo / conocido), descripción libre, fecha desde cuándo se conocen, nivel de cercanía.

#### 3. Persona → **TipoRelacion** (catálogo)
Un catálogo de tipos: *hermano, primo, colega, vecino, pareja...* con su categoría (familiar, amistad, profesional) y si es simétrico o no.

#### 4. Persona ↔ Grupo (N:M)
Los grupos permiten organizar personas: *familia García*, *amigos del instituto*, *trabajo actual*...
Una persona puede pertenecer a varios grupos; un grupo puede tener varias personas.

#### 5. Persona → **Evento** (1:N) — opcional
Registra interacciones: una llamada, una comida, un cumpleaños... con fecha, descripción y personas involucradas.
Si un evento puede involucrar a varias personas, sería N:M entre Evento y Persona.

---

### Esquema resumido

```
Persona ──< Contacto
Persona >──< Persona  (a través de Relacion, con TipoRelacion como catálogo)
Persona >──< Grupo
Persona ──< Evento  (o Persona >──< Evento si es grupal)
```

---

### Preguntas para ajustar el diseño

1. **¿Las relaciones son siempre entre dos personas**, o quieres registrar eventos/grupos donde interactúan varias?
2. **¿El tipo de relación es libre** (texto) o prefieres un catálogo cerrado (familiar, amigo, conocido)?
3. **¿Necesitas historial?** Por ejemplo, dos personas que fueron pareja y ahora son amigos.
4. **¿Eventos/interacciones** son importantes para ti, o el foco es solo quién es quién?
5. **¿Grupos** o solo las relaciones directas entre personas son suficientes?




## Diseño simplificado

---

### Entidad: Persona

| Atributo | Notas |
|---|---|
| id | clave primaria |
| nombre | |
| primer_apellido | |
| segundo_apellido | nullable |
| apodo | nullable |
| fecha_nacimiento | nullable |
| fecha_defuncion | nullable |
| notas | texto libre, nullable |

---

### Entidad: TipoRelacion

El catálogo de tipos. La clave de diseño es que cada tipo conoce su **inverso**.

| Atributo | Notas |
|---|---|
| id | clave primaria |
| nombre | "Padre", "Hijo", "Hermano", "Amigo"... |
| inverso_id | FK → TipoRelacion (el propio tipo si es simétrico) |

Ejemplos del catálogo:

| nombre | inverso |
|---|---|
| Padre | Hijo |
| Hijo | Padre |
| Hermano | Hermano *(apunta a sí mismo)* |
| Amigo | Amigo *(apunta a sí mismo)* |
| Tío | Sobrino |
| Sobrino | Tío |

---

### Entidad: Relacion

Une dos personas. Solo se guarda **una dirección**; la inversa se deduce.

| Atributo | Notas |
|---|---|
| id | clave primaria |
| persona_a_id | FK → Persona |
| persona_b_id | FK → Persona |
| tipo_id | FK → TipoRelacion (desde la perspectiva de persona_a) |

Si guardas `(Juan → Padre → María)`, puedes deducir automáticamente `(María → Hijo → Juan)` usando `inverso_id`.

---

### Diagrama Chen simplificado

```
[Persona] ────< tiene >──── [Relacion] ────> [TipoRelacion]
                 (1:N)    (persona_a, persona_b)   (N:1)
[Persona] ────< tiene >──┘
```

---

### Preguntas para ajustar

1. **¿Las relaciones tienen fecha?** Por ejemplo, *desde cuándo* son amigos, o cuándo se casaron.
2. **¿El catálogo de TipoRelacion es cerrado** (predefinido) o el usuario puede añadir tipos nuevos?
3. **¿Una relación puede tener notas propias?** Por ejemplo, "nos conocimos en el trabajo".


## Diseño final (por ahora)

---

### Entidad: Persona

| Atributo | |
|---|---|
| id | clave primaria |
| nombre | |
| primer_apellido | |
| segundo_apellido | nullable |
| apodo | nullable |
| fecha_nacimiento | nullable |
| fecha_defuncion | nullable |
| notas | nullable |

---

### Entidad: Relacion

| Atributo | |
|---|---|
| id | clave primaria |
| persona_a_id | FK → Persona |
| persona_b_id | FK → Persona |
| tipo | enum: `progenitor`, `pareja`, `amigo`, `conocido` |
| comentario | texto libre, nullable |

El campo `comentario` absorbe lo que antes llamábamos fecha, período, contexto... sin complicar el esquema. Por ejemplo: *"amigos desde el instituto, 1995-2003"* o *"pareja hasta 2010"*.

---

### Una observación sobre `progenitor`

Es el único tipo **asimétrico**: la dirección importa.
`persona_a` es progenitor de `persona_b`.

Para el resto (*pareja*, *amigo*, *conocido*) la dirección no importa: son simétricas.

Esto hay que tenerlo en cuenta al consultar la base de datos, pero no cambia el esquema.

---

¿Te parece bien así para empezar a codificar?

## Opciones para SQLite con FastAPI

---

### Cómo acceder a SQLite desde Python

**Opción A — SQLModel** *(recomendada)*
Creada por el mismo autor que FastAPI. Combina SQLAlchemy + Pydantic. Los modelos de base de datos y los modelos de la API son la misma clase. Muy poco código repetitivo.

**Opción B — SQLAlchemy**
El ORM más maduro y popular de Python. Más verboso que SQLModel pero con más documentación y más control. SQLModel se apoya en él por debajo.

**Opción C — sqlite3 puro**
Módulo de la librería estándar de Python. Sin ORM, SQL directo. Más trabajo manual pero sin dependencias externas.

Para este proyecto, **SQLModel** es la opción más natural junto a FastAPI.

---

### Docker con SQLite

Sí, funciona perfectamente. El truco es que SQLite es un **fichero**, no un servidor, así que hay que usar un **volumen Docker** para que los datos persistan cuando el contenedor se reinicia o se actualiza.

```
[Contenedor FastAPI]
    └── /app/data/fac.db  ←──── montado desde el host
                                 ~/fac-data/fac.db
```

Con Docker Compose sería un único servicio, muy sencillo:

```
fac/
├── docker-compose.yml
├── Dockerfile
├── app/
│   └── (código FastAPI)
└── data/          ← volumen SQLite (en el host)
    └── fac.db
```

No necesitas un contenedor separado para la base de datos (eso sería necesario con PostgreSQL o MySQL, no con SQLite).

---

### ¿Cuándo dejar SQLite y pasar a PostgreSQL?

SQLite tiene una limitación importante: **escrituras concurrentes**. Para un uso personal o de pocos usuarios simultáneos es más que suficiente. Si en el futuro el proyecto crece o necesita varios usuarios escribiendo a la vez, migrar a PostgreSQL con SQLAlchemy/SQLModel es sencillo porque solo cambia la cadena de conexión.

---

¿Te parece bien esta dirección? Si confirmas, puedo proponer la estructura de ficheros del proyecto antes de empezar a codificar.

## Estructura de ficheros propuesta

```
fac/
├── docker-compose.yml
├── Dockerfile
├── .env                        # variables de entorno (puerto, ruta DB, etc.)
├── .gitignore
├── requirements.txt
│
├── data/                       # volumen SQLite (ignorado por git)
│   └── fac.db
│
└── app/
    ├── main.py                 # entrada: crea la app FastAPI
    ├── database.py             # conexión y sesión SQLite/SQLModel
    ├── models.py               # tablas: Persona, Relacion
    ├── schemas.py              # modelos de entrada/salida de la API
    │
    ├── routers/
    │   ├── personas.py         # GET/POST/PUT/DELETE /personas
    │   └── relaciones.py       # GET/POST/PUT/DELETE /relaciones
    │
    └── static/
        ├── index.html          # interfaz principal
        ├── style.css
        └── app.js              # llamadas a la API (fetch)
```

---

### Por qué esta estructura

- `models.py` define las tablas con SQLModel
- `schemas.py` define qué datos entran y salen por la API (pueden diferir del modelo de BD)
- `routers/` separa los endpoints por entidad — fácil de ampliar
- `static/` sirve la interfaz HTML directamente desde FastAPI, sin servidor web aparte
- `data/` fuera de `app/` para que el volumen Docker no interfiera con el código

---

### Flujo de una petición

```
Navegador → app.js (fetch) → FastAPI router → SQLModel → fac.db
```

---

¿Algún ajuste antes de empezar a codificar?

Listo. Estructura completa creada. Para arrancarlo:

**Con Docker:**
```bash
docker compose up --build
```

**Sin Docker (local):**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Luego abre `http://localhost:8000`.

La documentación automática de la API está en `http://localhost:8000/docs`.
Listo. Resumen de los cambios:

**Backend** (`app/routers/personas.py`):
- Nuevo endpoint `GET /personas/{id}/arbol` que devuelve abuelos, padres, hermanos, parejas e hijos deducidos a partir de las relaciones `progenitor` y `pareja`.

**Frontend**:
- Botón 🌳 junto a cada persona en la lista
- Al pulsarlo, aparece el árbol debajo con 4 filas por generación:

```
Abuelos   [gris]  [gris]  [gris]  [gris]
Padres    [azul]  [azul]
Familia   [verde] [★PERSONA★] ♥ [pareja]
Hijos     [naranja] [naranja]
```

```bash
docker compose up --build
```
## Evaluar opciones para lenguaje natural

---

### Aclaración sobre MCP

MCP no es la herramienta adecuada aquí. MCP es un protocolo para conectar **Claude Desktop o Claude Code** a fuentes de datos externas (tu BD, ficheros, APIs). Serviría si quisieras hablarle a Claude Desktop y que él consultase tu app, pero no para poner una caja de texto dentro de la web.

Para lo que describes, las opciones reales son:

---

### Opción A — Claude API con Tool Use *(recomendada)*

El backend recibe el texto, lo envía a la API de Claude junto con definiciones de herramientas (`buscar_persona`, `crear_persona`, `crear_relacion`). Claude decide qué herramientas llamar y con qué parámetros. El backend ejecuta esas llamadas contra SQLite.

```
[Input usuario] → FastAPI → Claude API → tool calls → SQLite
```

**Pros:** Entiende cualquier frase, cualquier idioma, ambigüedades, nombres compuestos  
**Contras:** Requiere API key de Anthropic, coste por llamada (~fracción de céntimo), latencia ~1-2s  

---

### Opción B — Regex / reglas

Defines patrones fijos:
```
"X es padre de Y" → progenitor(X, Y)
"X y Y son amigos" → amigo(X, Y)
"X es pareja de Y" → pareja(X, Y)
```

**Pros:** Gratis, instantáneo, sin dependencias externas  
**Contras:** Cualquier variación rompe el parsing. "El padre de Juan es Ernesto" ya no funciona. Frágil.

---

### Opción C — LLM local (Ollama)

Añadir un contenedor Ollama con Llama 3 o Mistral. Sin coste por llamada.

**Pros:** Gratis, privado, sin API key  
**Contras:** Necesita bastante RAM/CPU, calidad inferior a Claude, añade complejidad al docker-compose, más lento en CPU

---

### Opción D — spaCy (NLP clásico)

Usar spaCy para extraer nombres propios + reglas para detectar el tipo de relación.

**Pros:** Gratis, ligero  
**Contras:** Los modelos de español son limitados, requiere bastante trabajo para casos reales, resultado similar a regex pero más complejo de implementar

---

### Comparativa

| | Calidad | Coste | Complejidad | Offline |
|---|---|---|---|---|
| Claude API | ★★★★★ | ~€0.001/llamada | Baja | No |
| Regex | ★★ | Gratis | Muy baja | Sí |
| Ollama | ★★★ | Gratis | Alta | Sí |
| spaCy | ★★★ | Gratis | Media | Sí |

---

### Mi recomendación

**Claude API con Tool Use** es la opción más sólida y la más rápida de implementar. La integración es directa desde FastAPI, sin infraestructura adicional. Si tienes ya una API key de Anthropic, el coste es despreciable para uso personal.

¿Quieres que lo implemente con esa opción?

Listo. Para ponerlo en marcha:

```bash
docker compose up --build
```

Después, la primera vez, hay que descargar el modelo (unos 2 GB):
```bash
docker compose exec ollama ollama pull llama3.2
```

Esto solo se hace una vez — el modelo queda guardado en el volumen `ollama_data`.

**Cómo funciona:** escribes una frase en la caja de texto, el backend la envía a Ollama con un prompt que le pide JSON estructurado, y con la respuesta busca las personas en la BD (o las crea si no existen) y añade las relaciones. La primera llamada puede tardar unos segundos mientras el modelo carga en memoria.