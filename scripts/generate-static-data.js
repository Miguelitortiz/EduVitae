const fs = require('fs');
const path = require('path');

// Usamos js-yaml desde node_modules de app-public (disponible via NODE_PATH)
const yaml = require('js-yaml');

async function main() {
  console.log('🔄 Iniciando generación de datos estáticos...');

  // 1. Caminos y directorios
  const projectRoot = path.join(__dirname, '..');
  const referenceDir = path.join(projectRoot, 'data', 'reference');
  const outputDir = path.join(projectRoot, 'services', 'app-public', 'src', 'content');
  const professorsOutputDir = path.join(outputDir, 'profesores');

  // Asegurar directorios de salida
  fs.mkdirSync(outputDir, { recursive: true });
  fs.mkdirSync(professorsOutputDir, { recursive: true });

  // 2. Cargar datos maestros locales (YAML) usando js-yaml
  let delegations = [];
  let careers = [];
  let faculties = [];
  try {
    delegations = yaml.load(fs.readFileSync(path.join(referenceDir, 'delegations.yaml'), 'utf-8')) || [];
    careers     = yaml.load(fs.readFileSync(path.join(referenceDir, 'careers.yaml'),     'utf-8')) || [];
    faculties   = yaml.load(fs.readFileSync(path.join(referenceDir, 'faculties.yaml'),   'utf-8')) || [];
    console.log(`✅ Datos de referencia cargados: ${delegations.length} delegaciones, ${careers.length} carreras, ${faculties.length} facultades.`);
  } catch (err) {
    console.error('❌ Error al leer los archivos YAML de referencia:', err);
    process.exit(1);
  }

  // 3. Conectar a PostgreSQL e intentar consultar datos
  let professors = [];
  let groups = [];

  const dbConfig = {
    connectionString: process.env.DATABASE_URL || `postgres://${process.env.DB_USER || 'admin'}:${process.env.DB_PASSWORD || 'admin_pass'}@${process.env.DB_HOST || 'localhost'}:${process.env.DB_PORT || '5432'}/${process.env.DB_NAME || 'eduvitae'}`,
    ssl: false
  };

  try {
    const { Client } = require('pg');
    const client = new Client(dbConfig);
    console.log(`🔌 Intentando conectar a la base de datos: ${dbConfig.connectionString.replace(/:[^:@]+@/, ':***@')}`);
    
    await client.connect();
    console.log('✅ Conexión a PostgreSQL establecida con éxito.');

    // Consultar profesores con sus career_ids agregados
    const profRes = await client.query(`
      SELECT p.id, p.slug, p.full_name, p.email, p.delegation_id, p.profile_data,
             COALESCE(
               json_agg(g.career_id) FILTER (WHERE g.career_id IS NOT NULL),
               '[]'
             ) as career_ids
      FROM professors p
      LEFT JOIN professor_groups pg ON p.id = pg.professor_id
      LEFT JOIN class_groups g ON pg.class_group_id = g.id
      GROUP BY p.id
      ORDER BY p.full_name ASC
    `);
    professors = profRes.rows.map(row => {
      const profile = row.profile_data;
      profile.id = row.id;
      profile.slug = row.slug;
      profile.fullName = row.full_name;
      profile.institutionalEmail = row.email;
      profile.delegation_id = row.delegation_id;
      profile.career_ids = row.career_ids;
      return profile;
    });

    // Consultar grupos
    const groupRes = await client.query('SELECT * FROM class_groups');
    const groupsRaw = groupRes.rows;

    // Consultar asignaciones
    const pgRes = await client.query('SELECT * FROM professor_groups');
    const assignments = pgRes.rows;

    // Estructurar grupos con sus profesores anidados
    groups = groupsRaw.map(g => {
      const groupAssignments = assignments.filter(a => a.class_group_id === g.id);
      const groupProfessors = groupAssignments.map(a => {
        const prof = professors.find(p => p.id === a.professor_id);
        return prof ? {
          id: prof.id,
          slug: prof.slug,
          fullName: prof.fullName,
          email: prof.institutionalEmail,
          subject_taught: a.subject_taught
        } : null;
      }).filter(p => p !== null);

      return {
        id: g.id,
        slug: g.slug,
        name: g.name,
        career_id: g.career_id,
        academic_period: g.academic_period,
        shift: g.shift,
        professors: groupProfessors
      };
    });

    await client.end();
    console.log(`✅ Base de datos consultada con éxito: ${professors.length} profesores, ${groups.length} grupos.`);
  } catch (err) {
    console.warn('⚠️ No se pudo conectar o consultar la base de datos. Usando fallback vacío. Detalle:', err.message);
    professors = [];
    groups = [];
    console.log('✅ Continuando con datos vacíos (BD no disponible en build).');
  }

  // 4. Escribir archivos de salida JSON
  try {
    // Datos de referencia maestros
    fs.writeFileSync(path.join(outputDir, 'delegations.json'), JSON.stringify(delegations, null, 2), 'utf-8');
    fs.writeFileSync(path.join(outputDir, 'careers.json'),     JSON.stringify(careers,     null, 2), 'utf-8');
    fs.writeFileSync(path.join(outputDir, 'faculties.json'),   JSON.stringify(faculties,   null, 2), 'utf-8');
    fs.writeFileSync(path.join(outputDir, 'groups.json'),      JSON.stringify(groups,      null, 2), 'utf-8');

    // Escribir cada profesor individualmente
    // Primero limpiar el directorio de profesores para no dejar archivos huérfanos
    const existingFiles = fs.readdirSync(professorsOutputDir).filter(f => f.endsWith('.json'));
    for (const file of existingFiles) {
      fs.unlinkSync(path.join(professorsOutputDir, file));
    }

    for (const prof of professors) {
      const profFile = path.join(professorsOutputDir, `${prof.slug}.json`);
      fs.writeFileSync(profFile, JSON.stringify(prof, null, 2), 'utf-8');
    }

    console.log(`🏁 Generación finalizada: ${delegations.length} delegaciones, ${faculties.length} facultades, ${careers.length} carreras, ${groups.length} grupos, ${professors.length} profesores.`);
  } catch (writeErr) {
    console.error('❌ Error al escribir los archivos JSON estáticos:', writeErr);
    process.exit(1);
  }
}

main();
