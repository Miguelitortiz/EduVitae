import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import pool from './db.js';

// Directorio de referencias YAML en runtime
const referenceDir = path.join(process.cwd(), 'data', 'reference');

export function cargarDelegaciones() {
  try {
    const fileContent = fs.readFileSync(path.join(referenceDir, 'delegations.yaml'), 'utf-8');
    return yaml.load(fileContent) || [];
  } catch (err) {
    console.error('Error al leer delegations.yaml en runtime:', err);
    return [];
  }
}

export function cargarCarreras() {
  try {
    const fileContent = fs.readFileSync(path.join(referenceDir, 'careers.yaml'), 'utf-8');
    return yaml.load(fileContent) || [];
  } catch (err) {
    console.error('Error al leer careers.yaml en runtime:', err);
    return [];
  }
}

export function cargarFacultades() {
  try {
    const fileContent = fs.readFileSync(path.join(referenceDir, 'faculties.yaml'), 'utf-8');
    return yaml.load(fileContent) || [];
  } catch (err) {
    console.error('Error al leer faculties.yaml en runtime:', err);
    return [];
  }
}

export function cargarFacultadesDeDelegacion(delegationId) {
  const faculties = cargarFacultades();
  return faculties.filter(f => f.delegation_id === delegationId);
}

export function cargarFacultadPorSlug(slug) {
  const faculties = cargarFacultades();
  return faculties.find(f => f.slug === slug) || null;
}

export function cargarCarrerasDeFacultad(faculty) {
  const allCareers = cargarCarreras();
  const careerIds = faculty.career_ids || [];
  return allCareers.filter(c => careerIds.includes(c.id));
}

export function cargarDelegacionPorSlug(slug) {
  const delegations = cargarDelegaciones();
  return delegations.find(d => d.slug === slug) || null;
}

export function cargarCarreraPorSlug(slug) {
  const careers = cargarCarreras();
  return careers.find(c => c.slug === slug) || null;
}

export function cargarCarrerasDeDelegacion(delegationId) {
  const careers = cargarCarreras();
  return careers.filter(c => c.delegation_id === delegationId);
}

export async function cargarGruposDeCarrera(careerId) {
  try {
    const res = await pool.query('SELECT * FROM class_groups WHERE career_id = $1 ORDER BY name ASC', [careerId]);
    return res.rows;
  } catch (err) {
    console.error(`Error al cargar grupos de carrera ${careerId} desde PostgreSQL:`, err);
    return [];
  }
}

export async function cargarGrupoConProfesores(g_slug) {
  try {
    const groupRes = await pool.query('SELECT * FROM class_groups WHERE slug = $1', [g_slug]);
    if (groupRes.rows.length === 0) return null;
    
    const grp = groupRes.rows[0];
    
    const profsRes = await pool.query(`
      SELECT p.slug, p.full_name as "fullName", p.email, pg.subject_taught
      FROM professors p
      JOIN professor_groups pg ON p.id = pg.professor_id
      WHERE pg.class_group_id = $1
      ORDER BY p.full_name ASC
    `, [grp.id]);
    
    return {
      id: grp.id,
      slug: grp.slug,
      name: grp.name,
      career_id: grp.career_id,
      academic_period: grp.academic_period,
      shift: grp.shift,
      professors: profsRes.rows
    };
  } catch (err) {
    console.error(`Error al cargar grupo con profesores para slug "${g_slug}" desde PostgreSQL:`, err);
    return null;
  }
}
