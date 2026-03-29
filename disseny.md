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