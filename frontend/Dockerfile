FROM node:18-alpine AS build
WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9.0.0 --activate

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package.json pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

RUN echo "VITE_API_BASE_URL=${VITE_API_BASE_URL}" > .env
RUN pnpm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
