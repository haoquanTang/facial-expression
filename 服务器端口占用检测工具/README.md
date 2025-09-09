# 服务器端口占用检测工具

一款功能强大的端口扫描和进程管理工具，支持本地和远程服务器端口检测，提供图形界面和命令行两种使用模式。

## 🚀 主要功能

- **端口扫描**：支持TCP和UDP协议的端口扫描
- **进程管理**：查看和终止占用端口的进程
- **远程支持**：通过SSH连接扫描远程服务器
- **双模式**：图形界面(GUI)和命令行(CLI)两种使用方式
- **多格式导出**：支持JSON、CSV、文本格式的结果导出
- **实时监控**：实时显示端口占用状态和进程信息

## 📋 系统要求

- **Python版本**：3.8 或更高版本
- **操作系统**：Windows 7+, macOS 10.15+, Linux (Ubuntu 18.04+)
- **内存**：最少 512MB
- **磁盘空间**：50MB

## 🛠️ 安装方法

### 方式一：从源码安装

```bash
# 1. 克隆项目
git clone https://github.com/your-username/port-scanner-tool.git
cd port-scanner-tool

# 2. 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python src/main.py
```

### 方式二：使用pip安装

```bash
# 安装项目
pip install -e .

# 运行程序
port-scanner
```

### 方式三：安装依赖库

如果只需要核心功能，可以手动安装依赖：

```bash
pip install psutil paramiko
```

## 🎯 使用方法

### GUI模式（图形界面）

```bash
# 启动GUI模式
python src/main.py
# 或
python src/main.py --gui
```

**GUI功能说明：**
- 左侧配置面板：设置扫描参数
- 右侧结果面板：显示扫描结果
- 支持本地和远程扫描模式切换
- 右键菜单：终止进程、查看详情、复制信息
- 结果导出：支持多种格式导出

### 命令行模式

#### 基本扫描

```bash
# 扫描单个端口
python src/main.py --port 8080

# 扫描端口范围
python src/main.py --range 8000-9000

# 扫描多个端口
python src/main.py --ports 80,443,8080,3306

# 混合格式
python src/main.py --ports 80,443,8000-8010
```

#### 进程管理

```bash
# 杀死占用指定端口的进程
python src/main.py --kill 8080
```

#### 远程扫描

```bash
# 使用密码认证
python src/main.py --remote 192.168.1.100 --user admin --password secret --range 80-443

# 使用密钥认证
python src/main.py --remote 192.168.1.100 --user admin --key ~/.ssh/id_rsa --range 80-443

# 指定SSH端口
python src/main.py --remote 192.168.1.100 --user admin --password secret --ssh-port 2222 --range 80-443
```

#### 输出格式

```bash
# 表格格式（默认）
python src/main.py --port 8080 --format table

# JSON格式
python src/main.py --port 8080 --format json

# CSV格式
python src/main.py --port 8080 --format csv

# 保存到文件
python src/main.py --port 8080 --format json --output result.json
```

#### 扫描选项

```bash
# 指定协议
python src/main.py --port 8080 --protocol tcp
python src/main.py --port 8080 --protocol udp
python src/main.py --port 8080 --protocol both

# 设置超时时间
python src/main.py --range 8000-9000 --timeout 2.0

# 设置线程数
python src/main.py --range 8000-9000 --threads 100

# 详细输出
python src/main.py --port 8080 --verbose

# 静默模式
python src/main.py --port 8080 --quiet
```

## 📊 输出示例

### 表格格式

```
扫描目标: localhost
扫描时间: 2024-01-15 10:30:45
扫描耗时: 2.34 秒
总端口数: 5
占用端口: 3
空闲端口: 2
占用率: 60.0%

+------+------+------+--------+-------------+-------------------+
| 端口  | 协议  | 状态  | 进程ID  | 进程名称      | 本地地址            |
+------+------+------+--------+-------------+-------------------+
| 80   | TCP  | 占用  | 1234   | nginx       | 0.0.0.0:80        |
| 443  | TCP  | 占用  | 1234   | nginx       | 0.0.0.0:443       |
| 8080 | TCP  | 占用  | 5678   | python      | 127.0.0.1:8080    |
+------+------+------+--------+-------------+-------------------+
```

### JSON格式

```json
{
  "scan_time": "2024-01-15T10:30:45",
  "scan_type": "local",
  "total_ports": 5,
  "occupied_ports": 3,
  "free_ports": 2,
  "occupation_rate": 60.0,
  "ports": [
    {
      "port": 80,
      "protocol": "TCP",
      "status": "LISTEN",
      "is_occupied": true,
      "local_address": "0.0.0.0:80",
      "pid": 1234,
      "process_name": "nginx"
    }
  ]
}
```

## 🔧 配置文件

### 应用配置 (config/settings.json)

```json
{
  "default_settings": {
    "scan_timeout": 5,
    "max_port_range": 1000,
    "log_level": "INFO",
    "thread_count": 50
  },
  "ui_settings": {
    "window_width": 900,
    "window_height": 700,
    "theme": "default"
  },
  "remote_settings": {
    "connection_timeout": 10,
    "command_timeout": 30
  }
}
```

### 远程服务器配置 (config/remote_servers.json)

```json
{
  "remote_servers": [
    {
      "name": "生产服务器",
      "host": "192.168.1.100",
      "username": "admin",
      "port": 22,
      "timeout": 10
    }
  ]
}
```

## 🚨 注意事项

### 权限要求

- **本地扫描**：某些端口信息需要管理员权限
- **进程终止**：终止其他用户的进程需要管理员权限
- **远程扫描**：需要目标服务器的SSH访问权限

### 安全建议

1. **密码安全**：避免在命令行中直接输入密码，使用配置文件或密钥认证
2. **权限控制**：谨慎使用进程终止功能，避免误杀系统关键进程
3. **网络安全**：远程扫描时确保网络连接安全

### 性能优化

1. **线程数量**：根据系统性能调整线程数，避免过高导致系统负载
2. **超时设置**：根据网络状况调整超时时间
3. **端口范围**：避免扫描过大的端口范围

## 🐛 故障排除

### 常见问题

**1. 权限不足错误**
```bash
# Linux/Mac
sudo python src/main.py

# Windows
# 以管理员身份运行命令提示符
```

**2. 远程连接失败**
- 检查网络连通性：`ping 目标IP`
- 验证SSH服务：`ssh 用户名@目标IP`
- 确认防火墙设置

**3. GUI界面无法显示**
- 确认系统支持图形界面
- 检查tkinter安装：`python -c "import tkinter"`
- 尝试使用命令行模式

**4. 依赖库安装失败**
```bash
# 更新pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 日志文件

日志文件位置：`logs/port_scanner.log`

可以通过查看日志文件获取详细的错误信息。

## 🏗️ 项目结构

```
port_scanner/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── main.py            # 主入口文件
│   ├── gui/               # GUI界面模块
│   │   ├── main_window.py # 主窗口
│   │   └── remote_config.py # 远程配置窗口
│   ├── core/              # 核心功能模块
│   │   ├── scanner.py     # 端口扫描
│   │   ├── process_manager.py # 进程管理
│   │   └── remote_client.py # 远程连接
│   ├── cli/               # 命令行接口
│   │   └── command_line.py
│   ├── models/            # 数据模型
│   │   └── data_models.py
│   └── utils/             # 工具模块
│       ├── config.py      # 配置管理
│       └── logger.py      # 日志管理
├── tests/                 # 测试代码
├── config/                # 配置文件
├── docs/                  # 文档
├── logs/                  # 日志文件
├── requirements.txt       # 依赖列表
├── setup.py              # 安装脚本
└── README.md             # 项目说明
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 提交Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

- **问题反馈**：[GitHub Issues](https://github.com/your-username/port-scanner-tool/issues)
- **功能建议**：[GitHub Discussions](https://github.com/your-username/port-scanner-tool/discussions)
- **邮件联系**：support@portscanner.com

## 🎉 致谢

感谢以下开源项目：

- [psutil](https://github.com/giampaolo/psutil) - 系统和进程信息库
- [paramiko](https://github.com/paramiko/paramiko) - SSH客户端库
- [tkinter](https://docs.python.org/3/library/tkinter.html) - Python GUI库

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**