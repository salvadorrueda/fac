let previewActual = null;

document.getElementById('form-nl').addEventListener('submit', async (e) => {
    e.preventDefault();
    const texto = document.getElementById('input-nl').value.trim();
    if (!texto) return;

    const btn = document.getElementById('btn-nl');
    const msg = document.getElementById('msg-nl');
    btn.disabled = true;
    btn.textContent = 'Procesando...';
    msg.textContent = '';
    ocultarPreview();

    const res = await fetch('/interpretar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto }),
    });
    const data = await res.json();

    btn.disabled = false;
    btn.textContent = 'Interpretar';

    if (res.ok) {
        previewActual = data;
        mostrarPreview(data);
    } else {
        msg.textContent = `Error: ${data.detail}`;
    }
});

function mostrarPreview(preview) {
    const div = document.getElementById('nl-preview');
    const mapaIndice = {};
    preview.personas.forEach(p => { mapaIndice[p.indice] = p; });

    const lineasPersonas = preview.personas.map(p => {
        const nombre = `${p.nombre} ${p.primer_apellido}${p.segundo_apellido ? ' ' + p.segundo_apellido : ''}`;
        return p.es_nueva
            ? `<span class="preview-nuevo">+ ${nombre} <em>(nueva)</em></span>`
            : `<span class="preview-existente">· ${nombre} <em>(ya existe)</em></span>`;
    });

    const lineasRelaciones = preview.relaciones.map(r => {
        const a = mapaIndice[r.persona_a];
        const b = mapaIndice[r.persona_b];
        const na = `${a.nombre} ${a.primer_apellido}`;
        const nb = `${b.nombre} ${b.primer_apellido}`;
        return `<span class="preview-nuevo">+ ${na} → <strong>${r.tipo}</strong> → ${nb}</span>`;
    });

    const sinCambios = preview.personas.every(p => !p.es_nueva) && preview.relaciones.length === 0;

    div.innerHTML = `
        <div class="preview-lista">
            ${lineasPersonas.join('')}
            ${lineasRelaciones.join('')}
            ${sinCambios ? '<span class="preview-existente">Sin cambios — todo ya existe en la base de datos.</span>' : ''}
        </div>
        <div class="preview-acciones">
            ${!sinCambios ? '<button onclick="confirmarPreview()">✓ Confirmar</button>' : ''}
            <button class="btn-secundario" onclick="cancelarPreview()">✕ Cancelar</button>
        </div>
    `;
    div.classList.remove('hidden');
}

function ocultarPreview() {
    document.getElementById('nl-preview').classList.add('hidden');
    previewActual = null;
}

function cancelarPreview() {
    ocultarPreview();
    document.getElementById('msg-nl').textContent = '';
}

async function confirmarPreview() {
    if (!previewActual) return;

    const res = await fetch('/interpretar/confirmar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preview: previewActual }),
    });
    const data = await res.json();
    ocultarPreview();

    const msg = document.getElementById('msg-nl');
    if (res.ok) {
        const partes = [];
        if (data.personas_creadas.length) partes.push(`Personas: ${data.personas_creadas.join(', ')}`);
        if (data.relaciones_creadas) partes.push(`${data.relaciones_creadas} relación(es)`);
        msg.textContent = `✓ ${partes.join(' · ')}`;
        document.getElementById('input-nl').value = '';
        await loadPersonas();
        await loadRelaciones();
    } else {
        msg.textContent = `Error: ${data.detail}`;
    }
}

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
    div.className = `arbol-tarjeta${esProtagonista ? ' protagonista' : ' clickable'}`;
    div.innerHTML = `
        <strong>${p.nombre} ${p.primer_apellido}</strong>
        ${p.segundo_apellido ? `<br>${p.segundo_apellido}` : ''}
        ${p.apodo ? `<br><em>(${p.apodo})</em>` : ''}
        ${p.fecha_nacimiento ? `<br><small>${p.fecha_nacimiento}${p.fecha_defuncion ? ' – ' + p.fecha_defuncion : ''}</small>` : ''}
    `;
    if (!esProtagonista) {
        div.onclick = () => verArbol(p.id);
    }
    return div;
}

function cerrarArbol() {
    document.getElementById('arbol-container').classList.add('hidden');
}

async function vaciarDB() {
    if (!confirm('¿Seguro que quieres borrar todos los datos? Esta acción no se puede deshacer.')) return;
    await fetch('/vaciar', { method: 'DELETE' });
    await loadPersonas();
    await loadRelaciones();
    cerrarArbol();
}

document.getElementById('input-importar').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const form = new FormData();
    form.append('file', file);

    const msg = document.getElementById('msg-importar');
    msg.textContent = 'Importando...';

    const res = await fetch('/importar', { method: 'POST', body: form });
    const data = await res.json();

    if (res.ok) {
        msg.textContent = `✓ ${data.personas_creadas} personas y ${data.relaciones_creadas} relaciones importadas`;
        await loadPersonas();
        await loadRelaciones();
    } else {
        msg.textContent = `Error: ${data.detail}`;
    }
    e.target.value = '';
    setTimeout(() => { msg.textContent = ''; }, 5000);
});

loadPersonas();
loadRelaciones();
