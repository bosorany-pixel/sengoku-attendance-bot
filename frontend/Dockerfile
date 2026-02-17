# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build for production under /mordor/ with API at /mordor/api
ARG VITE_BASE_PATH=/mordor/
ARG VITE_API_URL=/mordor/api
ENV VITE_BASE_PATH=$VITE_BASE_PATH
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Serve app under /mordor/ (for host nginx proxy at https://ya.sergeiscv.ru/mordor/)
COPY --from=builder /app/dist /usr/share/nginx/html/mordor

# Copy nginx config (serve /mordor/ and proxy /mordor/api to api service)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
