FROM node:20-alpine AS base

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci

COPY apps/web/ .

# Dev stage with hot reload
FROM base AS dev
CMD ["npm", "run", "dev"]

# Build stage
FROM base AS builder
ARG NEXT_PUBLIC_API_URL=/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Production stage
FROM node:20-alpine AS prod
WORKDIR /app

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
EXPOSE 3000
CMD ["node", "server.js"]
