FROM node:20-alpine AS build
WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9.0.0 --activate

ENV HUSKY=0
ARG VITE_API_BASE_URL
ARG VITE_SITE_HOSTNAME
ARG VITE_UMAMI_WEBSITE_ID

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_SITE_HOSTNAME=${VITE_SITE_HOSTNAME}
ENV VITE_UMAMI_WEBSITE_ID=${VITE_UMAMI_WEBSITE_ID}

COPY package.json pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

RUN echo "VITE_API_BASE_URL=${VITE_API_BASE_URL}" > .env
RUN echo "VITE_UMAMI_WEBSITE_ID=${VITE_UMAMI_WEBSITE_ID}" >> .env
RUN pnpm build && pnpm prune --prod --ignore-scripts

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
