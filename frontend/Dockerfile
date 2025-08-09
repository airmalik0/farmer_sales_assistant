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

# Build the application for production
RUN npm run build

# Production stage - minimal image with built files
FROM busybox:1.35

WORKDIR /app

# Copy built assets from builder stage
COPY --from=builder /app/dist ./dist

# Keep container running (nginx will serve files via volume)
CMD ["sh", "-c", "while true; do sleep 3600; done"]