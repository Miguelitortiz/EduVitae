import pg from 'pg';

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL || 'postgres://admin:admin_pass@postgres:5432/eduvitae'
});

export default pool;
