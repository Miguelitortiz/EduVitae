# EduVitae - Portal Académico e Extractor Curricular

EduVitae se ha reorganizado en una arquitectura de múltiples subproyectos para separar la visualización pública de la administración y extracción de datos. Este repositorio ahora se compone de dos aplicaciones principales construidas con **Astro** y estilizadas con **Tailwind CSS (v4)** usando una paleta de colores unificada basada en verde académico (`#527630`):

1. **`App` (Vitrina Pública)**: Portal web estático y optimizado para mostrar los perfiles académicos de profesores investigadores.
2. **`CV-UI` (Herramienta Administrativa)**: Interfaz local que permite subir currículums oficiales en formato PDF (Universidad de Colima), extraer su información mediante scripts de Python, editar los datos en un formulario amigable y exportar el perfil resultante directamente a la vitrina pública.

---

## 📁 Estructura del Repositorio

```
EduVitae/
├── App/                     # Sitio web público del claustro docente
│   ├── src/
│   │   ├── content/
│   │   │   └── profesores/  # Archivos JSON con los perfiles de los docentes
│   │   ├── components/      # Componentes visuales (IdentityCard, PublicationList, etc.)
│   │   └── ...
│   ├── package.json         # Ejecuta en puerto 6767
│   └── ...
├── CV-UI/                   # Interfaz de extracción y edición
│   ├── cv_extractor/        # Carpeta con scripts de Python y almacenamiento temporal
│   │   ├── cv_scraper.py    # Extractor de datos de PDF a JSON
│   │   ├── format_cv.py     # Adaptador de JSON para exportar a App
│   │   └── ...
│   ├── src/
│   │   ├── pages/
│   │   │   └── index.astro  # Editor visual y cargador de PDF
│   │   └── ...
│   ├── server.js            # Servidor backend de Node.js (Express, puerto 6769)
│   ├── package.json         # Ejecuta en puerto 6768
│   └── ...
└── README.md                # Esta guía general
```

---

## ⚙️ Requisitos Previos

- **Node.js** v22 o superior.
- **Python 3** con las librerías necesarias para la extracción (entorno virtual `venv`).
- **npm** para la gestión de paquetes de Node.

---

## 🚀 Guía de Inicio Rápido

Las aplicaciones corren en puertos distintos para poder ejecutarlas en paralelo sin conflictos:

### 1. Servidor de la Vitrina Pública (`App`)
Para iniciar el portal de consulta pública:
```bash
cd App
npm install
npm run dev
```
La aplicación estará disponible en: **`http://localhost:6767/`**

Para generar la compilación estática de producción (`dist/`):
```bash
npm run build
```

---

### 2. Panel Administrativo (`CV-UI`)
Esta aplicación requiere ejecutar tanto el frontend (puerto `6768`) como un backend en Node (Express en puerto `6769`) para interactuar con los scripts de Python.

#### Ejecución Estándar:
```bash
cd CV-UI
npm install
npm run dev
```
La aplicación estará disponible en: **`http://localhost:6768/`**

#### Ejecución mediante Distrobox (Recomendado en Fedora Kinoite):
Si desarrollas dentro de un contenedor Distrobox llamado `dev-main`, puedes arrancar el servidor directamente con:
```bash
distrobox enter dev-main -- npm run dev
```

---

## 🐍 Integración de Python y Flujo de Trabajo

El backend de `CV-UI` (`server.js`) interactúa de forma directa con los scripts de Python del directorio `cv_extractor`. 

### Entorno Virtual (`venv`)
Se requiere un entorno virtual de Python instalado en el proyecto para asegurar que las dependencias de extracción de PDF estén disponibles. El backend busca automáticamente el intérprete de Python en las siguientes rutas (por orden de prioridad):
- `CV-UI/venv/bin/python`
- `CV-UI/.venv/bin/python`
- `App/venv/bin/python`
- `App/.venv/bin/python`
- `/var/home/Moi/Documents/Projects/EduVitae/App/venv/bin/python`

### Flujo de Carga de un Docente:
1. **Subida y Extracción**: Desde la interfaz de `CV-UI` en el navegador, se sube el PDF del currículum. El backend ejecuta `cv_scraper.py` para parsear el contenido y devolver un JSON estructurado.
2. **Edición Curricular**: La interfaz muestra los campos extraídos (Grados académicos, artículos, docencia, tesis, etc.) permitiendo corregir errores de escaneo u omisiones.
3. **Exportación**: Al presionar **Listo (Exportar)**, el backend guarda los datos y ejecuta `format_cv.py`. Este script adapta la estructura final del docente y la escribe directamente como un archivo JSON en:
   `/var/home/Moi/Documents/Projects/EduVitae/App/src/content/profesores/[nombre-del-docente].json`
4. **Visualización**: La web de `App` leerá este nuevo JSON automáticamente en la siguiente compilación o recarga en caliente del entorno de desarrollo.
