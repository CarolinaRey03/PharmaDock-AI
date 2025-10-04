/**
 * Applies consistent styling to molecular viewer for protein-ligand visualization.
 * 
 * @param {Object} viewer - The 3Dmol.js viewer instance
 * @returns {Object} The styled viewer instance for chaining
 */
function get3DMolStyle(viewer) {
    //Style for receptor (model 0)
    viewer.setStyle({ model: 0 }, { cartoon: { color: 'spectrum' } });
    viewer.addStyle({ model: 0, hetflag: false, not: { elem: 'H' } },
        { stick: { radius: 0.15, colorscheme: "whiteCarbon", opacity: 0.8 } });

    // Style for ligand (model 1) - make it more visible with distinct colors
    viewer.setStyle({ model: 1 }, {
        stick: {
            radius: 0.3,
            colorscheme: "magentaCarbon",
            opacity: 1.0
        }
    });

    // Add sphere representation to make ligand more visible
    viewer.addStyle({ model: 1 }, {
        sphere: {
            radius: 0.5,
            colorscheme: "magentaCarbon",
            opacity: 0.9
        }
    });

    return viewer
}