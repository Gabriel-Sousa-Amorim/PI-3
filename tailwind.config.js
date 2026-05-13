module.exports = {
  darkMode: 'class',            // ESSENCIAL
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html', // se usar apps com templates internos
    './static/js/**/*.js',      // se houver JS com classes
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}