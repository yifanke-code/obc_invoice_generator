# Docker Volume 快速参考

## 最关键的 Volume 配置

### 问题：invoice_data.json 在根目录中，如何设置 volume？

### 答案：使用这个 docker-compose.yml

```yaml
volumes:
  - ./:/app                                              # 整个项目
  - ./invoice_data.json:/app/invoice_data.json:rw       # 配置文件
  - ./uploads:/app/uploads:rw                           # 上传文件
  - ./output:/app/output:rw                             # 输出文件
```

---

## 快速启动

```bash
# 1. 进入项目目录
cd /path/to/obc_invoice_generator

# 2. 确保目录存在
mkdir -p uploads output

# 3. 启动容器
docker-compose up -d

# 4. 检查状态
docker-compose ps
docker-compose logs -f
```

---

## 验证同步是否工作

### 测试 1：主机 → 容器

```bash
# 在主机上修改文件
echo '{"test": true}' > invoice_data.json

# 在容器内检查
docker exec obc-invoice-generator cat /app/invoice_data.json
# 应该能看到修改后的内容
```

### 测试 2：容器 → 主机

```bash
# 通过 Web UI 修改配置并保存

# 在主机上检查文件
cat ./invoice_data.json
# 应该能看到容器内的修改
```

---

## NAS 部署路径示例

| 组件 | 主机路径 | 容器路径 | 备注 |
|---|---|---|---|
| 项目根目录 | `/share/homes/admin/obc_invoice_generator` | `/app` | 整个项目 |
| 配置文件 | `/share/homes/admin/obc_invoice_generator/invoice_data.json` | `/app/invoice_data.json` | **关键** |
| 上传目录 | `/share/homes/admin/obc_invoice_generator/uploads` | `/app/uploads` | 照片 |
| 输出目录 | `/share/homes/admin/obc_invoice_generator/output` | `/app/output` | PDF |

---

## 权限设置

```bash
# 配置文件（可读可写）
chmod 666 invoice_data.json

# 目录（可读可写可执行）
chmod 777 uploads output
```

---

## 常见错误和解决方案

| 错误 | 原因 | 解决方案 |
|---|---|---|
| `Permission denied` | 目录权限不足 | `chmod 777 uploads output` |
| `No such file or directory` | 路径不存在 | `mkdir -p uploads output` |
| 修改看不到 | Volume 没有正确挂载 | 检查 docker-compose.yml 中的路径 |
| 容器写入失败 | 文件权限问题 | 确保文件 644 以上权限，目录 755 以上 |

---

## 手动 docker run 命令

如果使用 `docker run` 而不是 `docker-compose`：

```bash
docker run -d \
  --name obc-invoice-generator \
  -p 5050:5050 \
  -v $(pwd):/app \
  -v $(pwd)/invoice_data.json:/app/invoice_data.json:rw \
  -v $(pwd)/uploads:/app/uploads:rw \
  -v $(pwd)/output:/app/output:rw \
  -e PYTHONUNBUFFERED=1 \
  --restart unless-stopped \
  obc-invoice
```

**在 NAS 上使用绝对路径**：

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

---

## 常用命令

```bash
# 启动
docker-compose up -d

# 停止
docker-compose stop

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec obc-invoice /bin/bash

# 重启
docker-compose restart

# 完全删除（包括容器）
docker-compose down

# 删除容器和数据
docker-compose down -v
```

---

## 重要提示

✅ **invoice_data.json 在根目录时**：
- 使用 `./invoice_data.json:/app/invoice_data.json:rw`
- 这样容器内的修改会立即同步到主机
- 主机的修改容器也能立即看到

⚠️ **避免的做法**：
- ❌ 不要把 invoice_data.json 放在 templates 目录中
- ❌ 不要忘记 `:rw` 权限标志
- ❌ 不要使用不存在的路径

---

## 什么是 `:rw` 标志？

- `rw` = read-write（读写）
- `ro` = read-only（只读）

**示例**：
```yaml
- ./invoice_data.json:/app/invoice_data.json:rw  # 容器可读可写
- ./config:/app/config:ro                        # 容器只能读取
```
