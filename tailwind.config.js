/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // Super important pour la bascule de ta capture !
  theme: {
    extend: {
      colors: {
        // Mode clair (ton beige/bleuté très doux en fond)
        light: {
          bg: '#F0F2F9',       // Fond de l'application à droite
          sidebar: '#FFFFFF',  // Fond de la sidebar claire
          text: '#1E293B',     // Texte principal sombre
          hover: '#F1F5F9',    // Survol des liens
        },
        // Mode sombre (gris anthracite très élégant, pas noir pur)
        dark: {
          bg: '#12131A',       // Fond de l'application à droite
          sidebar: '#1C1D24',  // Fond de la sidebar sombre
          text: '#F8FAFC',     // Texte clair
          hover: '#262833',    // Survol des liens sombre
        },
        // Ta couleur d'accentuation (le bleu violet qu'on voit sur l'onglet actif "HOSPITAL")
        brand: {
          primary: '#4F46E5',  // Indigo vibrant pour l'élément sélectionné
          textActive: '#FFFFFF'
        }
      }
    },
  },
  plugins: [],
}