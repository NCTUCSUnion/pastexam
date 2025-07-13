# PastExam

A full-stack web application for managing and sharing past exam materials, built with Vue.js frontend and FastAPI backend.

## Project Structure

```
pastexam/
├── frontend/          # Vue.js 3 + Vite frontend
├── backend/           # FastAPI Python backend
├── docker/            # Docker configuration files
└── proxy/             # Nginx reverse proxy
```

## Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.11 or higher)
- **Docker** and **Docker Compose**
- **uv** (Python package manager)

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/NCTUCSUnion/pastexam.git
cd pastexam
```

### 2. Start infrastructure services

```bash
cd docker
docker compose -f docker-compose.dev.yml up -d
```

### 3. Backend setup

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

## Development

### Frontend Development

#### Project setup

```bash
cd frontend
npm install
```

#### Compiles and hot-reloads for development

```bash
npm run dev
```

#### Compiles and minifies for production

```bash
npm run build
```

#### Linting & Formatting

**ESLint**

```bash
npm run lint
# or
npx eslint --ext .js,.vue src
```

**Prettier**

```bash
npm run format
# or
npx prettier --write .
```

### Backend Development

#### Project setup

```bash
cd backend
uv sync
```

#### Run development server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Run tests

```bash
uv run pytest
```

## Docker Deployment

### Development Environment

```bash
cd docker
docker compose -f docker-compose.dev.yml up -d
```

### Production Environment

```bash
cd docker
docker compose up -d
```

## Environment Variables

### Backend (.env)

```env
# Database
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=your_db_name
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379

# MinIO
MINIO_ROOT_USER=your_minio_user
MINIO_ROOT_PASSWORD=your_minio_password

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Configuration

### Frontend Configuration

The frontend configuration is handled through Vite and can be customized in `frontend/vite.config.js`.

### Backend Configuration

Backend configuration is managed through Pydantic settings in `backend/app/core/config.py`.

## API Documentation

Once the backend is running, you can access the interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

### Frontend Tests

```bash
cd frontend
npm run test
```

### Backend Tests

```bash
cd backend
uv run pytest
```

## Build for Production

### Frontend Build

```bash
cd frontend
npm run build
```

### Backend Build

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Deployment

### Using Docker Compose

```bash
cd docker
docker compose up -d
```

### Manual Deployment

1. Build the frontend: `npm run build`
2. Start the backend: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Configure Nginx to serve the frontend and proxy to the backend

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please:

1. Check the [Issues](https://github.com/your-repo/issues) page
2. Create a new issue with detailed information
3. Contact the development team
