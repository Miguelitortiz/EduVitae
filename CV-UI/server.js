import express from 'express';
import cors from 'cors';
import multer from 'multer';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 6769;

app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Configurar multer para almacenar PDFs en cv_extractor/temp
const uploadDir = path.join(__dirname, 'cv_extractor', 'temp');
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    await fs.mkdir(uploadDir, { recursive: true });
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    cb(null, `uploaded_${Date.now()}.pdf`);
  }
});
const upload = multer({ storage });

/**
 * Detecta el intérprete de Python en el sistema.
 */
async function detectPython() {
  const potentialPaths = [
    path.join(__dirname, 'venv', 'bin', 'python'),
    path.join(__dirname, 'venv', 'bin', 'python3'),
    path.join(__dirname, '.venv', 'bin', 'python'),
    path.join(__dirname, '.venv', 'bin', 'python3'),
    path.join(__dirname, '..', 'App', 'venv', 'bin', 'python'),
    path.join(__dirname, '..', 'App', 'venv', 'bin', 'python3'),
    path.join(__dirname, '..', 'App', '.venv', 'bin', 'python'),
    path.join(__dirname, '..', 'App', '.venv', 'bin', 'python3'),
    '/var/home/Moi/Documents/Projects/EduVitae/App/venv/bin/python',
    '/var/home/Moi/Documents/Projects/EduVitae/App/venv/bin/python3',
  ];

  for (const p of potentialPaths) {
    try {
      await fs.access(p);
      return p;
    } catch {
      // Ignorar e intentar el siguiente
    }
  }
  return 'python3';
}

/**
 * Ejecuta un script de Python de forma asíncrona.
 */
function runPythonScript(pythonExe, scriptPath, args, cwd) {
  return new Promise((resolve, reject) => {
    const proc = spawn(pythonExe, [scriptPath, ...args], { cwd });
    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(`El script de Python falló con código ${code}.\n\nDetalles del error:\n${stderr}`));
      }
    });

    proc.on('error', (err) => {
      reject(err);
    });
  });
}

// Endpoint para procesar la subida del PDF y correr cv_scraper.py
app.post('/api/extract', upload.single('pdf'), async (req, res) => {
  let tempJsonPath = null;
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No se recibió ningún archivo PDF.' });
    }

    const tempPdfPath = req.file.path;
    const cvExtractorDir = path.join(__dirname, 'cv_extractor');
    const scraperScript = path.join(cvExtractorDir, 'cv_scraper.py');

    const tempJsonName = `cv_extracted_${Date.now()}_${Math.random().toString(36).substring(2, 9)}.json`;
    tempJsonPath = path.join(cvExtractorDir, tempJsonName);

    const pythonExe = await detectPython();

    // Ejecutar extractor indicándole el archivo temporal destino
    await runPythonScript(pythonExe, scraperScript, [tempPdfPath, tempJsonPath], cvExtractorDir);

    // Leer el JSON generado
    const jsonContent = await fs.readFile(tempJsonPath, 'utf-8');
    const parsedData = JSON.parse(jsonContent);

    // Limpiar archivos temporales
    await fs.unlink(tempPdfPath).catch(() => {});
    await fs.unlink(tempJsonPath).catch(() => {});

    return res.status(200).json(parsedData);
  } catch (err) {
    console.error('Error en /api/extract:', err);
    if (req.file) {
      await fs.unlink(req.file.path).catch(() => {});
    }
    if (tempJsonPath) {
      await fs.unlink(tempJsonPath).catch(() => {});
    }
    return res.status(500).json({ error: err.message || 'Error interno al procesar el PDF.' });
  }
});

// Endpoint para guardar el JSON de edición y correr format_cv.py
app.post('/api/save', async (req, res) => {
  let tempJsonPath = null;
  try {
    const body = req.body;
    if (!body) {
      return res.status(400).json({ error: 'No se recibieron datos para guardar.' });
    }

    const cvExtractorDir = path.join(__dirname, 'cv_extractor');
    const tempJsonName = `temp_save_${Date.now()}_${Math.random().toString(36).substring(2, 9)}.json`;
    tempJsonPath = path.join(cvExtractorDir, tempJsonName);

    // 1. Escribir datos editados a un archivo temporal único
    await fs.writeFile(tempJsonPath, JSON.stringify(body, null, 2), 'utf-8');

    // 2. Ejecutar formateador
    const pythonExe = await detectPython();
    const formatterScript = path.join(cvExtractorDir, 'format_cv.py');
    const destDir = path.join(__dirname, '..', 'EduVitae', 'src', 'content', 'profesores');

    await runPythonScript(pythonExe, formatterScript, [tempJsonPath, destDir], cvExtractorDir);

    // Limpiar archivo temporal
    await fs.unlink(tempJsonPath).catch(() => {});

    return res.status(200).json({ success: true, message: 'Perfil guardado y exportado con éxito a EduVitae.' });
  } catch (err) {
    console.error('Error en /api/save:', err);
    if (tempJsonPath) {
      await fs.unlink(tempJsonPath).catch(() => {});
    }
    return res.status(500).json({ error: err.message || 'Error interno al exportar los datos.' });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor backend de CV-UI corriendo en http://localhost:${PORT}`);
});
