# Stage 1: Build
FROM node:22-alpine AS build
WORKDIR /app

# Copiar package definitions del subproyecto
COPY services/app-public/package*.json ./services/app-public/

# Instalar dependencias en el subproyecto
RUN cd services/app-public && npm install --legacy-peer-deps

# Copiar el resto del código fuente del monorepo
COPY data ./data
COPY scripts ./scripts
COPY services/app-public ./services/app-public

# Correr script para generar los JSONs estáticos usando las dependencias de app-public
ARG DATABASE_URL
ENV DATABASE_URL=$DATABASE_URL
RUN NODE_PATH=./services/app-public/node_modules node scripts/generate-static-data.js

# Compilar la aplicación estática Astro
RUN cd services/app-public && npm run build

# Stage 2: Runtime
FROM node:22-alpine AS runtime
WORKDIR /app

# Copiar package.json del subproyecto
COPY services/app-public/package*.json ./services/app-public/

# Instalar dependencias de producción
RUN cd services/app-public && npm install --omit=dev --legacy-peer-deps

# Copiar el output compilado y los datos de referencia
COPY --from=build /app/services/app-public/dist ./services/app-public/dist
COPY --from=build /app/data ./data

# Exponer el puerto del servidor Astro
EXPOSE 80

# Definir variables de entorno de red y ejecutar el servidor standalone
ENV HOST=0.0.0.0
ENV PORT=80
CMD ["node", "services/app-public/dist/server/entry.mjs"]
