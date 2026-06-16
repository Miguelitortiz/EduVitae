# EduVitae - Claustro Académico e Investigadores

EduVitae es una aplicación web estática para mostrar perfiles académicos formales de profesores investigadores. Está construida sobre el framework **Astro** y estilizada mediante **Tailwind CSS (v4)** siguiendo un diseño editorial académico sobrio (inspirado en revistas científicas y anuarios de prestigio).

---

## 1. Requisitos Previos

Asegúrate de contar con:
- **Node.js** v18 o superior.
- **npm** (gestor de paquetes de Node).

---

## 2. Instrucciones de Uso y Comandos

### Instalar dependencias
Para instalar todas las dependencias necesarias de Astro y Tailwind CSS, ejecuta en la raíz del proyecto:
```bash
npm install
```

### Ejecutar en entorno de desarrollo
Inicia el servidor local de desarrollo con recarga en tiempo real:
```bash
npm run dev
```
El sitio estará disponible en: `http://localhost:4321/`

### Compilar para producción
Genera el sitio web completamente estático optimizado en la carpeta `dist/`:
```bash
npm run build
```
*(Nota: Para verificar localmente la compilación de producción, puedes ejecutar `npm run preview` después de hacer el build).*

---

## 3. Arquitectura y Estructura de Archivos

```
src/
├── content/
│   └── profesores/
│       ├── walter-mata.json       # Datos curados del Dr. Walter Mata
│       └── sofia-ramirez.json     # Datos de prueba (coherentes)
├── layouts/
│   └── InstitutionalLayout.astro  # Layout HTML5, SEO y envoltorio institucional
├── components/
│   ├── IdentityCard.astro         # Columna izquierda: Foto sepia/B&W y datos personales
│   ├── PublicationList.astro      # Central: Lista de artículos (impacto) y libros
│   ├── TeachingList.astro         # Central: Cursos impartidos (tablas) y tesis
│   ├── ImpactSidebar.astro        # Columna derecha: Indicadores numéricos de impacto
│   └── TeacherGrid.astro          # Rejilla del listado general en /docentes
├── lib/
│   └── cargarProfesores.js        # Utilidad de carga de datos JSON en tiempo de build
└── styles/
    └── global.css                 # Reset CSS, fuentes de Google y configuración Tailwind v4
```

---

## 4. Guía para Agregar un Nuevo Docente

Para agregar un perfil docente al directorio, realiza los siguientes dos pasos:

### Paso A: Crear el archivo JSON
Crea un nuevo archivo con el formato `nombre-del-docente.json` dentro de la carpeta `src/content/profesores/`. El archivo debe seguir estrictamente este esquema estructurado:

```json
{
  "slug": "nombre-del-docente",
  "fullName": "Nombre Completo del Docente",
  "photoUrl": "/images/profesores/nombre-del-docente.jpg",
  "title": "Puesto Académico (ej: Profesor Investigador de Tiempo Completo)",
  "department": "Nombre de la Facultad o Departamento",
  "institutionalEmail": "correo@ucol.mx",
  "admissionYear": 2005,
  "quote": "Frase inspiracional o académica del docente",
  "academicFormation": {
    "doctorados": [
      {
        "degree": "Doctor en...",
        "institution": "Universidad de...",
        "year": 2015
      }
    ],
    "maestrias": [
      {
        "degree": "Maestría en...",
        "institution": "Universidad de...",
        "year": 2008
      }
    ],
    "licenciatura": {
      "degree": "Licenciatura en...",
      "institution": "Universidad de...",
      "year": 2003
    }
  },
  "scientificProduction": {
    "articles": [
      {
        "title": "Título del artículo científico",
        "journal": "Nombre de la revista",
        "year": 2024,
        "impactFactor": 2.5,
        "doi": "https://doi.org/..."
      }
    ],
    "books": [
      {
        "title": "Título del libro publicado",
        "role": "Coautor o Coordinador",
        "editorial": "Nombre de la editorial",
        "year": 2023
      }
    ]
  },
  "educationalMaterials": [
    {
      "title": "Título del recurso didáctico",
      "type": "Recurso digital o Manual",
      "year": 2024,
      "url": "https://..."
    }
  ],
  "teaching": {
    "courses": [
      {
        "name": "Nombre de la materia",
        "level": "Licenciatura o Maestría",
        "students": 30,
        "period": "Ago-Ene 2025"
      }
    ],
    "theses": [
      {
        "student": "Nombre del alumno",
        "title": "Título de la tesis",
        "year": 2024,
        "role": "Asesor o Codirector"
      }
    ]
  },
  "certifications": [
    {
      "title": "Certificación Obtenida",
      "institution": "Institución Certificadora",
      "year": 2022
    }
  ],
  "academicBody": {
    "name": "Nombre del Cuerpo Académico",
    "level": "CAEC / CA en Consolidación / En Formación"
  }
}
```

> **Nota Crítica de Calidad**: Asegúrate de **excluir** todo dato puramente administrativo (como número de empleado, horas específicas de gestión o códigos de evaluación del tipo `I.II.X`).

### Paso B: Agregar la fotografía
1. Consigue una fotografía formal del docente.
2. Conviértela a formato **JPG** o **WebP** y colócala en `public/images/profesores/nombre-del-docente.jpg`.
3. El sistema aplicará de manera automática los filtros de estilo de anuario (escala de grises, contraste aumentado y ligero sepia). Si no se proporciona una imagen o no se encuentra el archivo, la tarjeta mostrará un elegante monograma con las iniciales del docente.

---

## 5. Despliegue en Netlify / Vercel

Debido a que EduVitae compila en modo estático puro (`static`), puede ser desplegado de forma gratuita con velocidad de carga extrema:

1. **Vercel / Netlify**: Conecta tu repositorio de Git.
2. **Comando de construcción**: `npm run build`
3. **Carpeta de salida**: `dist`
4. Dado que Astro gestiona las rutas estáticas automáticamente, las páginas `/docentes` y `/docentes/[slug]` funcionarán directamente sin necesidad de configuraciones especiales de redirección del servidor.
