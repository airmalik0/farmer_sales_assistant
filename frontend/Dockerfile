# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build arguments
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the application
RUN npm run build

# Production stage - minimal image to serve built files
FROM busybox:1.35

WORKDIR /app

# Copy built assets from builder stage
COPY --from=builder /app/dist ./dist

# Simple HTTP server for development/testing if needed
# In production, main nginx will serve these files via volume mount
EXPOSE 3000

# Keep container running
CMD ["sh", "-c", "while true; do sleep 3600; done"]