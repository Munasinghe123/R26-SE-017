# Stage 1: Build React App
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY apps/web/package*.json ./

RUN npm ci

# Copy web source code
COPY apps/web/ ./

# Build production bundle
RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx reverse proxy configuration
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf

# Copy static assets from build stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
