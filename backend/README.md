# pastexam API

1. Install [uv](https://docs.astral.sh/uv) if it is not already available:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. From the `backend` directory, run:

   ```bash
   uv sync
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Open [http://localhost:8000/docs](http://localhost:8000/docs) to load Swagger UI and exercise the API endpoints.

## Updating the Database Schema

1. Update the models

   Edit `backend/app/models/models.py`:

   ```python
   # Example: add a new column
   class User(SQLModel, table=True):
      id: Optional[int] = Field(default=None, primary_key=True)
      name: str
      email: str
      # New column
      phone: Optional[str] = None  # Added column
   ```

2. Create a migration

   ```bash
   cd backend
   uv run migrate.py create "Add phone field to User table"
   ```

3. Inspect the generated migration

   Check the new file under `backend/alembic/versions/` to ensure the diff is correct.

4. Apply the migration

   ```bash
   uv run migrate.py upgrade

   docker compose down
   docker compose up -d
   ```

## Migration Management Commands

```bash
cd backend

# Create a new migration
uv run migrate.py create "Your migration message"

# Apply all pending migrations
uv run migrate.py upgrade

# Show the current database revision
uv run migrate.py current

# Show migration history
uv run migrate.py history

# Downgrade to a specific revision (use with caution!)
uv run migrate.py downgrade <revision_id>
```
