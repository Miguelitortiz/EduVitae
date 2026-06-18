/**
 * Carga todos los perfiles de docentes desde los archivos JSON en src/content/profesores/
 * utilizando import.meta.glob de Vite.
 */
export async function cargarProfesores() {
  const modules = import.meta.glob('../content/profesores/*.json', { eager: true });
  return Object.values(modules).map(mod => mod.default || mod);
}

/**
 * Carga un docente específico a partir de su slug.
 * @param {string} slug 
 */
export async function cargarProfesor(slug) {
  const profesores = await cargarProfesores();
  return profesores.find(p => p.slug === slug) || null;
}
