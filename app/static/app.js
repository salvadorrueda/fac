async function loadPersonas() {
    const res = await fetch('/personas/');
    const personas = await res.json();

    const lista = document.getElementById('lista-personas');
    const selectA = document.querySelector('select[name="persona_a_id"]');
    const selectB = document.querySelector('select[name="persona_b_id"]');

    lista.innerHTML = '';
    selectA.innerHTML = '<option value="">Persona A</option>';
    selectB.innerHTML = '<option value="">Persona B</option>';

    personas.forEach(p => {
        const nombre = nombreCompleto(p);

        const li = document.createElement('li');
        li.innerHTML = `<span class="info">${nombre}</span><button class="btn-arbol" onclick="verArbol(${p.id})">🌳</button><button onclick="deletePersona(${p.id})">✕</button>`;
        lista.appendChild(li);

        [selectA, selectB].forEach(sel => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = nombre;
            sel.appendChild(opt);
        });
    });
}

async function loadRelaciones() {
    const [relRes, perRes] = await Promise.all([
        fetch('/relaciones/'),
        fetch('/personas/')
    ]);
    const relaciones = await relRes.json();
    const personas = await perRes.json();

    const mapa = {};
    personas.forEach(p => { mapa[p.id] = nombreCompleto(p); });

    const lista = document.getElementById('lista-relaciones');
    lista.innerHTML = '';

    relaciones.forEach(r => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span class="info">
                ${mapa[r.persona_a_id] || '?'} → <strong>${r.tipo}</strong> → ${mapa[r.persona_b_id] || '?'}
                ${r.comentario ? `<br><span class="comentario">${r.comentario}</span>` : ''}
            </span>
            <button onclick="deleteRelacion(${r.id})">✕</button>
        `;
        lista.appendChild(li);
    });
}

function nombreCompleto(p) {
    let n = `${p.nombre} ${p.primer_apellido}`;
    if (p.segundo_apellido) n += ` ${p.segundo_apellido}`;
    if (p.apodo) n += ` (${p.apodo})`;
    return n;
}

async function deletePersona(id) {
    await fetch(`/personas/${id}`, { method: 'DELETE' });
    await loadPersonas();
    await loadRelaciones();
}

async function deleteRelacion(id) {
    await fetch(`/relaciones/${id}`, { method: 'DELETE' });
    await loadRelaciones();
}

document.getElementById('form-persona').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    Object.keys(data).forEach(k => { if (data[k] === '') delete data[k]; });

    await fetch('/personas/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    e.target.reset();
    await loadPersonas();
});

document.getElementById('form-relacion').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    data.persona_a_id = parseInt(data.persona_a_id);
    data.persona_b_id = parseInt(data.persona_b_id);
    if (data.comentario === '') delete data.comentario;

    await fetch('/relaciones/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    e.target.reset();
    await loadRelaciones();
});

async function verArbol(id) {
    const res = await fetch(`/personas/${id}/arbol`);
    const arbol = await res.json();

    document.getElementById('arbol-titulo').textContent =
        `Árbol de ${nombreCompleto(arbol.persona)}`;

    const contenido = document.getElementById('arbol-contenido');
    contenido.innerHTML = '';

    const filas = [
        { label: 'Abuelos', personas: arbol.abuelos, clase: 'nivel-abuelos' },
        { label: 'Padres',  personas: arbol.padres,  clase: 'nivel-padres'  },
        { label: 'Pareja',  personas: arbol.parejas, clase: 'nivel-pareja'  },
        { label: 'Hijos',   personas: arbol.hijos,   clase: 'nivel-hijos'   },
    ];

    // Fila central: hermanos + persona + pareja
    const filasCentral = buildFilaCentral(arbol);
    contenido.appendChild(buildFila('Abuelos', arbol.abuelos, 'nivel-abuelos'));
    contenido.appendChild(buildFila('Padres', arbol.padres, 'nivel-padres'));
    contenido.appendChild(filasCentral);
    contenido.appendChild(buildFila('Hijos', arbol.hijos, 'nivel-hijos'));

    document.getElementById('arbol-container').classList.remove('hidden');
    document.getElementById('arbol-container').scrollIntoView({ behavior: 'smooth' });
}

function buildFila(label, personas, clase) {
    const fila = document.createElement('div');
    fila.className = `arbol-fila ${clase}`;
    fila.innerHTML = `<span class="arbol-label">${label}</span>`;
    const grupo = document.createElement('div');
    grupo.className = 'arbol-grupo';
    if (personas.length === 0) {
        grupo.innerHTML = '<span class="arbol-vacio">—</span>';
    } else {
        personas.forEach(p => grupo.appendChild(tarjetaPersona(p, false)));
    }
    fila.appendChild(grupo);
    return fila;
}

function buildFilaCentral(arbol) {
    const fila = document.createElement('div');
    fila.className = 'arbol-fila nivel-central';
    fila.innerHTML = '<span class="arbol-label">Familia</span>';
    const grupo = document.createElement('div');
    grupo.className = 'arbol-grupo';

    arbol.hermanos.forEach(p => grupo.appendChild(tarjetaPersona(p, false)));
    grupo.appendChild(tarjetaPersona(arbol.persona, true));
    arbol.parejas.forEach(p => {
        const sep = document.createElement('span');
        sep.className = 'arbol-sep';
        sep.textContent = '♥';
        grupo.appendChild(sep);
        grupo.appendChild(tarjetaPersona(p, false));
    });

    fila.appendChild(grupo);
    return fila;
}

function tarjetaPersona(p, esProtagonista) {
    const div = document.createElement('div');
    div.className = `arbol-tarjeta${esProtagonista ? ' protagonista' : ''}`;
    div.innerHTML = `
        <strong>${p.nombre} ${p.primer_apellido}</strong>
        ${p.segundo_apellido ? `<br>${p.segundo_apellido}` : ''}
        ${p.apodo ? `<br><em>(${p.apodo})</em>` : ''}
        ${p.fecha_nacimiento ? `<br><small>${p.fecha_nacimiento}${p.fecha_defuncion ? ' – ' + p.fecha_defuncion : ''}</small>` : ''}
    `;
    return div;
}

function cerrarArbol() {
    document.getElementById('arbol-container').classList.add('hidden');
}

loadPersonas();
loadRelaciones();
