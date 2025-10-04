/**
 * Initializes the 3D molecular viewer with sample molecules.
 * Fetches receptor and ligand data, renders them with styling,
 * and handles animation transitions.
 */
function initialize3DMol() {
    const element = document.querySelector('#container-01');
    element.classList.add('visible');
    let viewer = $3Dmol.createViewer(element, { backgroundColor: '#426553' });

    const receptorPath = '/static/img/molecules/2mm3.pdbqt';
    const posPath = '/static/img/molecules/2mm3_Abemaciclib_out.pdbqt';
    const ligandPath = '/static/img/molecules/2mm3_Abemaciclib_out.pdbqt.sdf'

    Promise.all([
        fetch(receptorPath).then(res => res.text()),
        fetch(posPath).then(res => res.text()),
        fetch(ligandPath).then(res => res.text())
    ])
        .then(([receptorData, posData, ligandData]) => {
            viewer.addModel(receptorData, "pdbqt");
            viewer.addModel(ligandData, "sdf");
            viewer.addModel(posData, "pdbqt");
            viewer = get3DMolStyle(viewer);
            viewer.zoomTo();
            viewer.render();
            viewer.zoom(1.2, 1000);
        })
        .catch(err => {
            console.error("Error loading models:", err.message);
        });
}

/**
 * Creates a typing animation with welcome messages.
 * Initializes the 3D viewer after typing animation completes.
 *
 * @param {Object} messages - Text messages to display in sequence
 */
function initializeTyped(messages) {
    console.log("Inicializando Typed.js...");
    var typed = new Typed("#typed", {
        strings: [
            messages.welcome_message,
            messages.explanation_message,
            messages.example_message,
            messages.docking_message
        ],
        typeSpeed: 20,
        startDelay: 500,
        backDelay: 1000,
        backSpeed: 20,
        showCursor: true,
        onComplete: function (self) {
            setTimeout(initialize3DMol, 800);
        }
    });
}

// Initialize typing animation when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    if (typeof messages !== 'undefined') {
        console.log("Messages found, starting the animation...");
        initializeTyped(messages);
    } else {
        console.error("Error: Variable 'messages' no encontrada");
    }
});
