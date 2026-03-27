# Docker 部署检查清单

## 📋 部署前检查

### 文件和目录结构

- [ ] `invoice_data.json` 在项目根目录（不在 templates 中）
- [ ] `docker-compose.yml` 存在
- [ ] `Dockerfile` 存在
- [ ] `uploads/` 目录存在
- [ ] `output/` 目录存在

```bash
# 验证命令
ls -la | grep -E "invoice_data|docker-compose|Dockerfile"
ls -la | grep -E "uploads|output"
```

### 文件权限

- [ ] invoice_data.json 可读可写 (664 或 666)
- [ ] uploads 目录可读写执行 (755 或 777)
- [ ] output 目录可读写执行 (755 或 777)

```bash
# 设置权限命令
chmod 666 invoice_data.json
chmod 755 uploads output
```

### 配置检查

- [ ] docker-compose.yml 语法正确

```bash
# 验证 docker-compose.yml 配置
docker-compose config
```

---

## 🚀 部署步骤

### 步骤 1：初始化

```bash
# 进入项目目录
cd /path/to/obc_invoice_generator

# 确保目录存在
mkdir -p uploads output

# 设置权限
chmod 666 invoice_data.json
chmod 755 uploads output
```

- [ ] 目录已创建
- [ ] 权限已设置

### 步骤 2：构建和启动

```bash
# 构建镜像
docker-compose build

# 启动容器
docker-compose up -d

# 检查状态
docker-compose ps
```

- [ ] Docker 镜像已构建
- [ ] 容器已启动
- [ ] 容器状态为 "Up"

### 步骤 3：验证日志

```bash
# 查看日志
docker-compose logs

# 应该看到类似输出：
# [OK] Registered Chinese font: C:\Windows\Fonts\SimsunExtG.ttf
# [INFO] Using font: ChineseFont
# * Running on http://0.0.0.0:5050
```

- [ ] 没有错误信息
- [ ] 中文字体已注册
- [ ] Flask 服务器正在运行

---

## 🔗 网络和端口检查

### 步骤 4：验证网络连接

```bash
# 检查容器网络
docker inspect obc-invoice-generator | grep -A 5 NetworkSettings

# 应该看到：
# "5050/tcp": [{"HostIp": "0.0.0.0", "HostPort": "5050"}]
```

- [ ] 端口 5050 已暴露
- [ ] 容器可以访问网络

### 步骤 5：测试 Web 访问

```bash
# 使用 curl 测试（如果有 WSL 或 Linux）
curl http://localhost:5050/

# 或在浏览器中访问
# http://<your-ip>:5050
```

- [ ] Web UI 可以访问
- [ ] 返回 HTML 页面（不是错误）

---

## 💾 Volume 同步检查

### 步骤 6：验证 Volume 挂载

```bash
# 检查 Volume 挂载点
docker inspect obc-invoice-generator | grep -A 20 Mounts

# 应该看到 4 个 mount：
# 1. /project -> /app
# 2. /project/invoice_data.json -> /app/invoice_data.json
# 3. /project/uploads -> /app/uploads
# 4. /project/output -> /app/output
```

- [ ] 4 个 volume 都已挂载
- [ ] 所有挂载点都是 "rw"（读写）

### 步骤 7：测试主机 → 容器 同步

```bash
# 修改主机上的 invoice_data.json
echo '{"timestamp": "'$(date +%s)'"}' > invoice_data.json

# 在容器内检查
docker exec obc-invoice-generator cat /app/invoice_data.json

# 或进入容器检查
docker-compose exec obc-invoice /bin/bash
cat /app/invoice_data.json
exit
```

- [ ] 容器能读到主机的修改
- [ ] 文件内容一致

### 步骤 8：测试容器 → 主机 同步

```bash
# 通过 Web UI 修改配置并保存

# 在主机上检查
cat invoice_data.json

# 或使用 docker 检查
docker exec obc-invoice-generator cat /app/invoice_data.json | diff - invoice_data.json
```

- [ ] 主机能看到容器的修改
- [ ] 文件内容一致

---

## 📁 文件和目录检查

### 步骤 9：检查生成的文件

```bash
# 查看 uploads 目录
ls -la uploads/

# 查看 output 目录
ls -la output/

# 应该能看到容器生成的文件
```

- [ ] uploads 目录可读写
- [ ] output 目录可读写
- [ ] 容器可以创建文件

---

## 🧪 功能测试

### 步骤 10：Web UI 功能测试

1. **加载配置**
   - [ ] 打开 http://<ip>:5050
   - [ ] Web UI 正常显示
   - [ ] 现有配置已加载

2. **修改配置**
   - [ ] 修改 FROM 信息
   - [ ] 修改 BILL TO 信息
   - [ ] 修改 PAYMENT 信息
   - [ ] 点击"保存"
   - [ ] 收到"已儲存"提示

3. **验证持久化**
   - [ ] 刷新页面
   - [ ] 修改的配置仍然存在
   - [ ] 检查 invoice_data.json 文件内容

4. **测试 PDF 生成**
   - [ ] 添加发票项目
   - [ ] 上传照片
   - [ ] 点击"產生 PDF"
   - [ ] PDF 生成成功
   - [ ] 文件出现在 output/ 目录

5. **测试 .obc 文件**
   - [ ] 点击"儲存 .obc"
   - [ ] 文件下载成功
   - [ ] 点击"開啟 .obc"
   - [ ] 可以重新加载保存的数据

---

## 🔧 故障排除

### 问题：容器无法启动

```bash
# 查看详细日志
docker-compose logs -f

# 重建镜像
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

- [ ] 已查看错误日志
- [ ] 已尝试重建镜像

### 问题：Volume 不同步

```bash
# 检查 docker-compose.yml 中的 volume 配置
cat docker-compose.yml | grep -A 5 volumes

# 检查文件权限
ls -la invoice_data.json
chmod 666 invoice_data.json

# 重启容器
docker-compose restart
```

- [ ] 已验证 volume 配置
- [ ] 已设置正确的文件权限
- [ ] 已重启容器

### 问题：权限错误

```bash
# 设置正确的权限
chmod 666 invoice_data.json
chmod 777 uploads output

# 验证权限
ls -la | grep -E "invoice_data|uploads|output"
```

- [ ] 已设置 666 权限给 invoice_data.json
- [ ] 已设置 777 权限给 uploads 和 output 目录

---

## ✅ 最终验证清单

在完成所有上述步骤后，检查以下项目：

### 系统运行

- [ ] Docker 容器正在运行（docker-compose ps）
- [ ] 没有错误日志（docker-compose logs）
- [ ] 可以在浏览器访问 Web UI

### 文件同步

- [ ] 主机修改 → 容器可见
- [ ] 容器修改 → 主机可见
- [ ] 实时同步（无延迟）

### 数据持久化

- [ ] invoice_data.json 在主机和容器中一致
- [ ] 重启容器后数据仍然存在
- [ ] 修改不会丢失

### 功能完整

- [ ] Web UI 正常运行
- [ ] 配置保存成功
- [ ] PDF 生成正常
- [ ] 照片上传正常
- [ ] .obc 文件导入导出正常

### 中文支持

- [ ] PDF 中的中文正确显示
- [ ] 没有乱码
- [ ] 字体已正确注册

---

## 📊 性能检查

```bash
# 查看容器资源使用
docker stats obc-invoice-generator

# 应该看到合理的 CPU 和内存使用率
```

- [ ] CPU 使用率正常（< 5% 空闲时）
- [ ] 内存使用率正常（< 200MB）

---

## 🎉 部署完成

当所有项目都已勾选后，您的部署就已完成！

**下一步**：
- 定期备份 invoice_data.json
- 监控容器日志
- 定期更新代码和依赖

**常用命令**：
```bash
docker-compose stop      # 停止容器
docker-compose start     # 启动容器
docker-compose restart   # 重启容器
docker-compose down      # 删除容器
docker-compose logs -f   # 查看日志
```
