# Step 1: Build Angular application
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build -- --configuration production

# Step 2: Serve with Nginx
FROM nginx:alpine

COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

# Custom nginx configuration for Angular SPA routing
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
