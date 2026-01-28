# -----------------------------------------------------------------------------
# STAGE 1: Dependency Install
# -----------------------------------------------------------------------------
FROM node:20-alpine AS deps
WORKDIR /app

# Install dependencies needed for native modules (if any)
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci

# -----------------------------------------------------------------------------
# STAGE 2: Builder
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for build time (Next.js inlines these)
# NOTE: In production, these should be provided by the CI/CD pipeline,
# but for local Docker Compose, we default them here or pass via build args.
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the Next.js application
RUN npm run build

# -----------------------------------------------------------------------------
# STAGE 3: Runtime Runner
# -----------------------------------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy only the necessary files for running the server
COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

# server.js is created by next build in the standalone directory
CMD ["node", "server.js"]