document.addEventListener('DOMContentLoaded', () => {
    const selectDepto = document.getElementById('filtroDepartamento');
    const inputAutor = document.getElementById('filtroAutor');
    const btnLimpiar = document.getElementById('limpiarFiltros');
    const filas = document.querySelectorAll('#tablaRelatos tbody .fila-relato');
    const mensajeVacio = document.getElementById('sinResultados');

    if (!selectDepto || !inputAutor || !btnLimpiar) {
        return;
    }

    function normalizarTexto(texto) {
        return (texto || '')
            .toString()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .trim();
    }

    function aplicarFiltros() {
        const deptoSeleccionado = normalizarTexto(selectDepto.value);
        const autorBuscado = normalizarTexto(inputAutor.value);
        let visibles = 0;

        filas.forEach(fila => {
            const deptoFila = normalizarTexto(fila.dataset.departamento);
            const autorFila = normalizarTexto(fila.dataset.autor);

            const coincideDepto = !deptoSeleccionado || deptoFila === deptoSeleccionado;
            const coincideAutor = !autorBuscado || autorFila.includes(autorBuscado);

            if (coincideDepto && coincideAutor) {
                fila.style.display = '';
                visibles++;
            } else {
                fila.style.display = 'none';
            }
        });

        if (mensajeVacio) {
            mensajeVacio.classList.toggle('d-none', visibles > 0);
        }
    }

    selectDepto.addEventListener('change', aplicarFiltros);
    inputAutor.addEventListener('input', aplicarFiltros);
    btnLimpiar.addEventListener('click', () => {
        selectDepto.value = '';
        inputAutor.value = '';
        aplicarFiltros();
    });
});