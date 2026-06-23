# EduVitae - Claustro Docente e Extractor Curricular (Monorepo)

EduVitae es una plataforma profesional, desacoplada y lista para producción, diseñada para gestionar y visualizar perfiles académicos de profesores investigadores adscritos a la Universidad de Colima.

Esta solución está organizada en un **Monorepo** orquestado mediante **Docker Compose** y cuenta con una arquitectura de múltiples subproyectos para separar la visualización pública (estática, compilada por SSG) del panel administrativo y extractor de datos (API dinámica y editor visual).

---

## 📁 Estructura del Monorepo

```
EduVitae/
├── data/
│   └── reference/
│       ├── delegations.yaml        # Lista inmutable de Delegaciones (ID, slug, name)
│       ├── careers.yaml            # Lista inmutable de Carreras (ID, slug, delegation_id, name)
│       └── seed_professors/        # Copias locales de respaldo de perfiles (para builds de Docker)
├── scripts/
│   ├── init.sql                    # Inicialización DDL de PostgreSQL + Datos Semilla
│   └── generate-static-data.js     # Script para leer referencias YAML y BD y generar JSONs estáticos
├── services/
│   ├── app-public/                 # Vitrina pública construida en Astro (SSG)
│   │   ├── src/
│   │   │   ├── content/            # Destino donde se volcarán los JSONs generados (Solo en build)
│   │   │   └── pages/              # Rutas anidadas para exploración estática
│   │   └── Dockerfile              # Construcción en Node, servido con Nginx
│   ├── admin-frontend/             # Panel administrativo para carga y edición (Astro)
│   │   ├── src/                    # Editor visual y cargador de PDF
│   │   └── Dockerfile              # Construcción estática servida por Nginx
│   ├── admin-backend/              # API Server (Express) + Python Extractor
│   │   ├── cv_extractor/           # Scripts de python para parsear y formatear PDF
│   │   ├── server.js               # API REST conectada a PostgreSQL
│   │   └── Dockerfile              # Imagen multinivel Node.js + Python 3
│   └── proxy/                      # Nginx Reverse Proxy para orquestación de tráfico
│       └── default.conf            # Reglas de enrutamiento
├── docker-compose.yml              # Orquestador del monorepo
├── .env.production                 # Variables de entorno de producción
└── README.md                       # Esta guía
```

---

## ⚙️ Reglas de Enrutamiento del Proxy (Nginx)

El servicio `proxy` expone el puerto `80` y enruta el tráfico interno de la siguiente manera:
- **`/`** (Raíz) &rarr; Dirige a `app-public` (Vitrina pública, 100% estática).
- **`/admin`** &rarr; Dirige a `admin-frontend` (Panel de edición y carga de PDFs).
- **`/api`** &rarr; Dirige a `admin-backend` (Endpoints REST, protegidos por Basic Auth).

---

## 🚀 Despliegue con Docker Compose (Recomendado)

Todo el ecosistema se levanta y se inicializa con un único comando:

1. **Configurar el archivo `.env.production`**:
   Asegúrate de configurar las credenciales deseadas para PostgreSQL y el Basic Auth de administración:
   ```env
   DB_USER=admin
   DB_PASSWORD=admin_pass
   ADMIN_USER=admin
   ADMIN_PASSWORD=admin_pass
   ```

2. **Iniciar la aplicación**:
   ```bash
   docker-compose up -d --build
   ```

3. **Verificar servicios**:
   - Accede a la **Vitrina Pública**: **`http://localhost/`**
   - Accede al **Panel Administrativo**: **`http://localhost/admin`**
     *(Las credenciales por defecto son `admin` / `admin_pass`)*

---

## 🗄️ Modelo de Datos (PostgreSQL)

El archivo `scripts/init.sql` inicializa las tablas necesarias al primer arranque de la base de datos:

1. **`professors`**: Almacena el identificador, slug, adscripción (delegation_id del YAML) y un JSONB `profile_data` con la estructura jerárquica curricular.
2. **`class_groups`**: Contiene los grupos dinámicos creados desde el panel (con referencia a la carrera del YAML).
3. **`professor_groups`**: Tabla intermedia que vincula los profesores con los grupos de clases y guarda la materia que imparten.

---

## 🔧 Script de Generación Estática (`generate-static-data.js`)

Durante el build del contenedor de la vitrina pública (`app-public`), se ejecuta `scripts/generate-static-data.js`:
1. Lee los archivos locales de referencia `delegations.yaml` y `careers.yaml`.
2. Intenta conectar a PostgreSQL para obtener el listado de docentes y sus grupos asignados.
3. **Mecanismo de Tolerancia (Build-Safe)**: Si la base de datos está offline o no es accesible en la compilación (por ejemplo, en compiladores de CI/CD aislados), el script registrará un *Warning* y cargará los perfiles desde la carpeta local de respaldo `data/reference/seed_professors/`, asegurando que la imagen de Docker siempre compile con éxito.
4. Escribe los archivos JSON resultantes en `services/app-public/src/content/`.
