<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/2950f4b0-f11d-46e4-98fb-28c0e701dcbc">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/user-attachments/assets/6125c7f1-5e26-4cfc-93dc-67a77720011d">
    <img alt="Pastexam banner" src="https://github.com/user-attachments/assets/6125c7f1-5e26-4cfc-93dc-67a77720011d">
  </picture>
  <h3>交大資工考古題系統</h3>
  <a href="https://github.com/NCTUCSUnion/pastexam/actions/workflows/main.yml"><img alt="CI/CD Pipeline" src="https://img.shields.io/github/actions/workflow/status/NCTUCSUnion/pastexam/main.yml?label=CI%2FCD%20Pipeline"></a>
  <a href="https://github.com/NCTUCSUnion/pastexam/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/NCTUCSUnion/pastexam?label=Release&color=mediumseagreen"></a>
  <img alt="Users" src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpastexam.nctucsunion.me%2Fapi%2Fstatistics&query=%24.data.totalUsers&label=Users">
  <img alt="Downloads" src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpastexam.nctucsunion.me%2Fapi%2Fstatistics&query=%24.data.totalDownloads&label=Downloads&color=darkcyan">
</div>

---

## 簡介

交大資工考古題系統是由[交大資工系學會](https://github.com/NCTUCSUnion)開發與維護的考古題平台，提供系上同學瀏覽、下載與分享歷年考試題目及解答。使用者需以陽明交通大學單一入口帳號（[NYCU OAuth](https://id.nycu.edu.tw/)）登入。

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/NCTUCSUnion/pastexam/umami/umami-dark.png">
    <img src="https://raw.githubusercontent.com/NCTUCSUnion/pastexam/umami/umami.png" alt="Usage analytics" width="820">
  </picture>
</p>

## 功能

- **瀏覽與篩選**：依課程、年份、教授與考試類型查找考古題。
- **預覽與下載**：線上預覽或下載 PDF。
- **上傳**：分享考古題給其他同學。
- **討論區**：針對每份考古題即時討論。
- **AI 模擬試題**：以 Google Gemini 根據考古題生成模擬試題。
- **管理後台**：管理課程、使用者與公告。

## 介面預覽

### 搜尋介面
<p align="center">
  <img src="docs/screenshots/search.webp" width="100%" />
</p>

### 文件預覽與討論區
<p align="center">
  <img src="docs/screenshots/preview-forum.webp" width="100%" />
</p>

### AI 模擬試題
<p align="center">
  <img src="docs/screenshots/ai-exam.webp" width="100%" />
</p>

## 技術

- **前端**：Vue 3、PrimeVue、Tailwind CSS
- **後端**：FastAPI、PostgreSQL、Redis
- **檔案儲存**：RustFS（S3 相容）
- **部署**：Docker Compose、GitHub Actions

## 本地開發

需求：Docker 與 Docker Compose v2。

```bash
git clone git@github.com:NCTUCSUnion/pastexam.git
cd pastexam

cp docker/.env.example docker/.env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker compose -f docker/docker-compose.dev.yml up -d --build
```

啟動後開啟 <http://localhost:8080>。

### 測試

```bash
docker compose -f docker/docker-compose.dev.yml run --rm backend uv run pytest   # 後端
cd frontend && pnpm install && pnpm test --run                                   # 前端
```

## 開發與部署

- 由 `dev` 建立分支，完成後開 Pull Request 合併回 `dev`；問題回報與建議請使用 [Issues](https://github.com/NCTUCSUnion/pastexam/issues)。
- Commit 訊息遵循 [Conventional Commits](https://www.conventionalcommits.org/)。
- `dev` 合併至 `main` 後會自動部署並發布新版本。

## 授權

本專案採用 [MIT License](LICENSE) 授權。

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/NCTUCSUnion">NCTUCSUnion</a>
</p>
