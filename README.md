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

### 方法 3：使用 Docker（推薦）

ASUSTOR 支援 Docker（需安裝 **Docker** App）。

建立 `Dockerfile`：
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5050
CMD ["python", "app.py"]
```

```bash
docker build -t obc-invoice .
docker run -d -p 5050:5050 \
  -v /share/homes/admin/obc_data:/app/uploads \
  -v /share/homes/admin/obc_data:/app/output \
  --name obc-invoice \
  --restart unless-stopped \
  obc-invoice
```

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

> **注意**：photos 的 `path` 是 NAS 上的絕對路徑（上傳後由 server 回傳）。


1. 讀檔及存檔.obc時，要包括from, bill to, payment的選項
2. 在OBC trip上面加上一欄invoice number, 並同時產生在PDF上、如果留空白，則pdf上就不用產生
3. 將invoice_data的位置，從/ 移到/templates下面
