# Docker Volume 配置指南

## 概述

由于 `invoice_data.json` 现在位于**项目根目录**中，我们需要确保 Docker volume 正确配置，使主机和容器之间的文件能够同步。

---

## 推荐方案：使用 docker-compose.yml

### 配置说明

```yaml
version: '3.8'

services:
  obc-invoice:
    build: .
    ports:
      - "5050:5050"
    volumes:
      # ① 挂载整个应用目录
      - ./:/app
      
      # ② 明确挂载 invoice_data.json（确保同步）
      - ./invoice_data.json:/app/invoice_data.json:rw
      
      # ③ 分别挂载 uploads 和 output 目录
      - ./uploads:/app/uploads:rw
      - ./output:/app/output:rw
    
    environment:
      - PYTHONUNBUFFERED=1
    
    container_name: obc-invoice-generator
    restart: unless-stopped
```

### 各 Volume 说明

| 挂载点 | 说明 | 权限 |
|---|---|---|
| `./:/app` | 整个项目目录 | 读写 |
| `./invoice_data.json:/app/invoice_data.json:rw` | **配置文件（关键）** | 读写 |
| `./uploads:/app/uploads:rw` | 上传的照片 | 读写 |
| `./output:/app/output:rw` | 生成的 PDF | 读写 |

---

## 启动步骤

### 1. 在主机上创建目录结构

```bash
# 进入项目目录
cd /path/to/obc_invoice_generator

# 确保这些目录存在
mkdir -p uploads output

# 确认 invoice_data.json 在根目录
ls -la invoice_data.json
```

### 2. 启动 Docker Compose

```bash
# 构建镜像并启动容器
docker-compose up -d

# 查看容器状态
docker-compose ps

# 查看日志（检查是否成功启动）
docker-compose logs -f
```

### 3. 验证 Volume 挂载

```bash
# 查看容器中的文件
docker exec obc-invoice-generator ls -la /app/

# 检查 invoice_data.json 是否存在
docker exec obc-invoice-generator cat /app/invoice_data.json
```

---

## invoice_data.json 同步工作流程

### 场景 1：修改主机上的文件

```
主机: 编辑 ./invoice_data.json
  ↓
Volume 同步（实时）
  ↓
容器内: /app/invoice_data.json 自动更新
  ↓
Web UI 刷新时读取最新数据
```

### 场景 2：通过 Web UI 修改（容器内保存）

```
Web UI: 点击"保存"按钮
  ↓
容器内: App 保存到 /app/invoice_data.json
  ↓
Volume 同步（实时）
  ↓
主机: ./invoice_data.json 自动更新
```

---

## NAS 部署示例（ASUSTOR）

### 假设您的 NAS 目录结构

```
/share/homes/admin/
├── obc_invoice_generator/      ← 项目目录
│   ├── docker-compose.yml
│   ├── app.py
│   ├── Dockerfile
│   ├── invoice_data.json       ← 配置文件（根目录）
│   ├── uploads/
│   └── output/
```

### NAS 上的启动命令

```bash
# SSH 登录 NAS
ssh admin@<NAS-IP>

# 进入项目目录
cd /share/homes/admin/obc_invoice_generator

# 启动 Docker Compose
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 常见问题排查

### 问题 1：invoice_data.json 在主机修改，但容器看不到

**原因**：Volume 没有正确挂载

**解决**：
```bash
# 检查挂载点
docker inspect obc-invoice-generator | grep -A 10 Mounts

# 应该看到类似的输出：
# "Mounts": [
#   {
#     "Type": "bind",
#     "Source": "/path/to/invoice_data.json",
#     "Destination": "/app/invoice_data.json",
#     "Mode": "rw"
#   }
# ]
```

### 问题 2：容器内修改，主机看不到

**原因**：权限问题或目录权限不足

**解决**：
```bash
# 检查文件权限
ls -la /share/homes/admin/obc_invoice_generator/invoice_data.json

# 确保有读写权限（666 或 644）
chmod 666 /share/homes/admin/obc_invoice_generator/invoice_data.json
```

### 问题 3：uploads 和 output 目录权限错误

**原因**：容器内无法写入主机目录

**解决**：
```bash
# 确保目录存在且有正确权限
mkdir -p /share/homes/admin/obc_invoice_generator/uploads
mkdir -p /share/homes/admin/obc_invoice_generator/output

chmod 777 /share/homes/admin/obc_invoice_generator/uploads
chmod 777 /share/homes/admin/obc_invoice_generator/output
```

---

## 手动 docker run 命令（不使用 docker-compose）

如果您不想使用 docker-compose.yml，可以使用以下命令：

```bash
docker run -d \
  --name obc-invoice-generator \
  -p 5050:5050 \
  -v /share/homes/admin/obc_invoice_generator:/app \
  -v /share/homes/admin/obc_invoice_generator/invoice_data.json:/app/invoice_data.json:rw \
  -v /share/homes/admin/obc_invoice_generator/uploads:/app/uploads:rw \
  -v /share/homes/admin/obc_invoice_generator/output:/app/output:rw \
  -e PYTHONUNBUFFERED=1 \
  --restart unless-stopped \
  obc-invoice
```

### 重要注意事项

- 使用**绝对路径**（例如 `/share/homes/admin/...` 而不是 `./`）
- Windows 路径需要使用 `/` 而不是 `\`（如使用 WSL2）
- 确保路径存在且有读写权限

---

## 文件权限最佳实践

### Docker Dockerfile 中的权限设置

```dockerfile
# 创建目录并设置权限
RUN mkdir -p /app/uploads /app/output && \
    chmod 755 /app/uploads /app/output && \
    touch /app/invoice_data.json && \
    chmod 666 /app/invoice_data.json
```

### 主机上的权限建议

```bash
# invoice_data.json - 允许容器读写
chmod 666 /path/to/invoice_data.json

# uploads 和 output 目录 - 允许容器写入
chmod 777 /path/to/uploads
chmod 777 /path/to/output
```

---

## 验证清单

在部署后，检查以下项目：

- [ ] `docker-compose ps` 显示容器正在运行
- [ ] `docker-compose logs` 没有错误
- [ ] 在浏览器访问 `http://<NAS-IP>:5050` 可以打开 Web UI
- [ ] 修改 Web UI 中的配置并保存
- [ ] 在主机上检查 `invoice_data.json` 是否已更新
- [ ] 修改主机上的 `invoice_data.json`
- [ ] 刷新 Web UI，确认显示最新数据
- [ ] 上传照片到 `uploads` 目录
- [ ] 生成 PDF 后检查 `output` 目录

---

## 停止和删除容器

```bash
# 停止容器（不删除）
docker-compose stop

# 启动容器
docker-compose start

# 停止并删除容器
docker-compose down

# 删除容器和所有数据
docker-compose down -v
```

---

## 总结

✅ **invoice_data.json 在根目录时的最佳配置**：

```yaml
volumes:
  - ./:/app
  - ./invoice_data.json:/app/invoice_data.json:rw
  - ./uploads:/app/uploads:rw
  - ./output:/app/output:rw
```

✅ **主要优点**：
- 配置文件与代码一起存储
- 容器启动快速（不需要复制）
- 主机和容器间实时同步
- 易于备份（整个目录都在一个位置）

✅ **关键文件权限**：
- `invoice_data.json`: `666`（读写）
- `uploads/` 目录: `777`（读写执行）
- `output/` 目录: `777`（读写执行）
