# OBC Invoice Generator — Web Server

透過瀏覽器使用的 Invoice 產生器，適合部署在 ASUSTOR NAS 上。

## 檔案結構

```
obc_invoice_server/
├── app.py               ← Flask 主程式
├── requirements.txt     ← Python 依賴
├── invoice_data.json    ← 自動產生：FROM/BILL TO/PAYMENT 常用資料
├── templates/
│   └── index.html       ← Web UI
├── static/
│   └── photo_placeholder.svg
├── uploads/             ← 上傳的照片（自動產生）
└── output/              ← 產生的 PDF（自動產生）
```

## 安裝

```bash
pip install -r requirements.txt
```

## 執行

```bash
python app.py
```

開啟瀏覽器：`http://<NAS-IP>:5050`

---

## ASUSTOR NAS 部署步驟

### 方法 1：SSH 直接執行

1. 在 NAS 上安裝 Python3（透過 App Central 安裝 **Python3**）
2. SSH 連線到 NAS：
   ```bash
   ssh admin@<NAS-IP>
   ```
3. 上傳此資料夾到 NAS（例如 `/share/homes/admin/obc_invoice/`）
4. 安裝依賴：
   ```bash
   pip3 install flask reportlab pillow pypdf
   ```
5. 執行：
   ```bash
   cd /share/homes/admin/obc_invoice
   python3 app.py
   ```
6. 瀏覽器開啟：`http://<NAS-IP>:5050`

### 方法 2：開機自動啟動（使用 /etc/rc.local）

在 `/etc/rc.local` 加入：
```bash
cd /share/homes/admin/obc_invoice && python3 app.py &
```

### 方法 3：使用 Docker Compose（推薦）

ASUSTOR 支援 Docker（需安裝 **Docker** App）。

最簡單的方式是使用 `docker-compose.yml`：

```bash
# 構建並啟動容器
docker-compose up -d

# 檢查運行狀態
docker-compose ps

# 停止容器
docker-compose down
```

`docker-compose.yml` 會自動：
- 構建 Docker 映像
- 在 5050 埠啟動服務
- 掛載 volume，使 `invoice_data.json` 能同步到主機目錄
- 設置自動重啟策略

**Volume 掛載說明**：
```yaml
volumes:
  - ./:/app                              # 整個應用目錄
  - ./invoice_data.json:/app/invoice_data.json:rw  # 設定檔
  - ./uploads:/app/uploads:rw            # 上傳的照片
  - ./output:/app/output:rw              # 產生的 PDF
```

### 方法 4：手動 Docker 命令

若不使用 docker-compose，可用以下命令：

```bash
# 構建映像
docker build -t obc-invoice .

# 運行容器（保持 volume 同步）
docker run -d -p 5050:5050 \
  -v $(pwd):/app \
  -v $(pwd)/invoice_data.json:/app/invoice_data.json:rw \
  -v $(pwd)/uploads:/app/uploads:rw \
  -v $(pwd)/output:/app/output:rw \
  --name obc-invoice \
  --restart unless-stopped \
  obc-invoice
```

**NAS 上的範例**（使用絕對路徑）：
```bash
docker run -d -p 5050:5050 \
  -v /share/homes/admin/obc_invoice:/app \
  -v /share/homes/admin/obc_invoice/invoice_data.json:/app/invoice_data.json:rw \
  -v /share/homes/admin/obc_invoice/uploads:/app/uploads:rw \
  -v /share/homes/admin/obc_invoice/output:/app/output:rw \
  --name obc-invoice \
  --restart unless-stopped \
  obc-invoice
```

**修改 invoice_data.json 後的同步**：
- 編輯主機上的 `invoice_data.json`
- 容器內會自動看到更新（因為掛載了 volume）
- 反之亦然：容器內保存的修改會自動出現在主機上

---

## API 端點

| Method | Path | 說明 |
|--------|------|------|
| GET | `/` | Web UI |
| GET | `/api/profiles` | 讀取 FROM/BILL TO/PAYMENT 資料 |
| POST | `/api/profiles` | 儲存 profiles |
| POST | `/api/upload_photo` | 上傳照片（multipart/form-data，欄位名 `photo`）|
| POST | `/api/generate_pdf` | 產生 PDF，回傳 `{"url": "/download/xxx.pdf"}` |
| GET | `/download/<filename>` | 下載 PDF |

## .obc 檔案格式

`.obc` 是純 JSON，可直接在 Web UI 存取，也可手動編輯：

```json
{
  "date": "2026-03-24",
  "inv_number": "INV-2026-001",
  "obc_trip": "Trip description",
  "from": { "full_name": "...", "street": "...", "post_code": "...", "city": "..." },
  "billto": { "company": "...", "address": "..." },
  "payment": { "payment": "...", "bank_name": "...", "beneficiary": "...",
               "swift": "...", "iban": "..." },
  "items": [{ "description": "Service", "cost": "100", "qty": "2" }],
  "notes": "...",
  "photos": [{ "path": "/absolute/path/on/server.jpg", "description": "..." }]
}
```

> **注意**：
> - `inv_number` 為選填（如果留空，PDF 上不會顯示）
> - `photos` 的 `path` 是 server 上的絕對路徑（上傳後由 server 回傳）
