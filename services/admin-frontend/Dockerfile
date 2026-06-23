# Stage 1: Build
FROM node:22-alpine AS build
WORKDIR /app

# Copiar package definitions del subproyecto
COPY services/admin-frontend/package*.json ./services/admin-frontend/

# Instalar dependencias
RUN cd services/admin-frontend && npm install

# Copiar código fuente
COPY services/admin-frontend ./services/admin-frontend

# Compilar Astro
RUN cd services/admin-frontend && npm run build

# Stage 2: Runtime
FROM nginx:alpine
# Copiar al subpath /admin para mapear la ruta del proxy
COPY --from=build /app/services/admin-frontend/dist /usr/share/nginx/html/admin
COPY services/admin-frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
