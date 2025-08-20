# pastexam API

1. 安裝 [uv](https://docs.astral.sh/uv)（若未安裝）：

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. 在 `backend` 目錄執行：

   ```bash
   uv sync
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. 開啟瀏覽器到 http://localhost:8000/docs，可看到 Swagger UI，並測試各 API。

## 修改資料庫 Schema

1. 修改 Models

   編輯 `backend/app/models/models.py`

   ```python
   # 例如：新增一個欄位
   class User(SQLModel, table=True):
      id: Optional[int] = Field(default=None, primary_key=True)
      name: str
      email: str
      # 新增的欄位
      phone: Optional[str] = None  # 新欄位
   ```

2. 建立 Migration

   ```bash
   cd backend
   uv run migrate.py create "Add phone field to User table"
   ```

3. 檢查生成的 Migration

   檢查 `backend/alembic/versions/` 中新生成的檔案，確認變更正確。

4. 應用 Migration

   ```bash
   uv run migrate.py upgrade

   docker compose down
   docker compose up -d
   ```

## Migration 管理指令

```bash
cd backend

# 建立新的 migration
uv run migrate.py create "Your migration message"

# 應用所有 pending migrations
uv run migrate.py upgrade

# 檢查目前的資料庫版本
uv run migrate.py current

# 查看 migration 歷史
uv run migrate.py history

# 回復到特定版本（謹慎使用！）
uv run migrate.py downgrade <revision_id>
```
