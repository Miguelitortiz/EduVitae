-- DDL Schema Setup

-- 1. Profesores (Almacena el perfil completo en JSONB)
CREATE TABLE professors (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    delegation_id INTEGER, -- SOLO referencia al ID del YAML, SIN FK a BD.
    profile_data JSONB NOT NULL, -- Aquí va grados, publicaciones, docencia, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Grupos (Dinámicos, editables por el admin)
CREATE TABLE class_groups (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,
    career_id INTEGER, -- SOLO referencia al ID del YAML de carreras, SIN FK a BD.
    name VARCHAR(50) NOT NULL,
    academic_period VARCHAR(50),
    shift VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Tabla Puente (Asignación Profesor <-> Grupo)
CREATE TABLE professor_groups (
    id SERIAL PRIMARY KEY,
    professor_id INTEGER NOT NULL REFERENCES professors(id) ON DELETE CASCADE,
    class_group_id INTEGER NOT NULL REFERENCES class_groups(id) ON DELETE CASCADE,
    subject_taught VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(professor_id, class_group_id)
);

-- Índices para búsquedas rápidas
CREATE INDEX idx_professors_delegation ON professors(delegation_id);
CREATE INDEX idx_groups_career ON class_groups(career_id);

