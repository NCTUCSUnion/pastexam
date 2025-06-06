# pastexam API

1. 安裝 [uv](https://docs.astral.sh/uv)（若未安裝）：

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. 在 `backend` 目錄執行：

   ```bash
   uv sync
   uv run uvicorn app:main --reload --host 0.0.0.0 --port 8000
   ```

3. 開啟瀏覽器到 http://localhost:8000/docs，可看到 Swagger UI，並測試各 API。
