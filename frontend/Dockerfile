# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy dependencies manifest
COPY package*.json ./

# Install packages
RUN npm install

# Copy source code files
COPY . .

# Compile and build production bundle
RUN npm run build

# Production stage
FROM nginx:1.25-alpine

# Copy assets
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
