# ArXiv 论文助手

ArXiv 论文助手是一个自动化工具，可以根据指定的关键词搜索 arXiv 上最新发布的论文，并通过邮件发送摘要和中文翻译。它使用 GitHub Actions 定时运行，无需服务器或本地环境。

## 核心功能

- 📝 **智能搜索** - 支持基础关键词搜索（匹配标题/摘要）
- 🌐 **智能翻译** - 使用 AI 服务将论文摘要翻译成中文
- 💡 **贡献总结** - 生成论文的一句话贡献要点
- 📧 **邮件推送** - 自动将论文信息以邮件形式发送到指定邮箱
- ⏰ **定时执行** - 利用 GitHub Actions 每天定时执行，无需手动操作

## 使用方法

### 1. 使用模板创建仓库

1. **使用模板创建新仓库**
   
   点击仓库顶部的 "Use this template" → "Create a new repository"
   
2. **设置仓库权限**
   - 进入仓库 "Settings" → "Actions" → "General"
   - 在 "Workflow permissions" 选择 "Read and write permissions"
   - 勾选 "Allow GitHub Actions to create and approve pull requests"

### 2. 配置邮箱和API

在您创建的仓库中:
- 进入 "Settings" > "Secrets and variables" > "Actions"
- 添加以下 secrets:

| 名称 | 说明 | 示例值 |
|------|------|--------|
| SENDER_EMAIL | 发件人邮箱 | 123456@qq.com |
| SENDER_NAME | 发件人名称 | ArXiv论文助手 |
| SENDER_PASSWORD | 邮箱授权码 | xxxxxxxx |
| RECEIVER_EMAILS | 收件人邮箱（多个用逗号分隔） | email1@example.com,email2@example.com |
| SMTP_SERVER | SMTP服务器地址 | smtp.qq.com |
| SMTP_PORT | SMTP服务器端口 | 465 |
| OPENAI_API_KEY | OpenAI 或其他兼容服务的 API 密钥 | sk-xxxxxxxxxxxxxxxx |
| OPENAI_MODEL | 使用的 AI 模型 | `deepseek-chat` |
| OPENAI_API_BASE | API 基础 URL | https://api.deepseek.com/v1 |
| SEARCH_TERMS | 搜索关键词（用逗号分隔） | "transformer","attention" |
| MAX_RESULTS | 每个关键词最大结果数 | 10 |

### 邮箱配置说明

#### QQ邮箱推荐配置
| 配置项 | 值 |
|--------|----|
| SMTP服务器 | smtp.qq.com |
| 端口 | 465 |
| 加密方式 | SSL |

#### 其他邮箱支持
支持任意SMTP邮箱服务，需要您自行查找：
1. SMTP服务器地址（如Gmail是`smtp.gmail.com`）
2. 端口号（通常为465/587）
3. 加密方式（SSL/TLS）
4. 授权码（非登录密码）

> 提示：搜索"您的邮箱服务商名称 SMTP设置"即可找到官方配置

## 搜索功能说明

### 当前支持的语法
```bash
# 基础关键词搜索（匹配标题/摘要）
vision transformer, large language model

# 固定顺序搜索
"vision transformer", "large language model"
```

## 常见问题

- **如何限定特定领域？**
   - 当前自动限定计算机科学（`cat:cs.*`）
   - 如需其他领域需要修改代码

- **QQ邮箱授权码获取**
   - 登录QQ邮箱 → 设置 → 账户 → 开启POP3/SMTP服务
   - 按照提示获取16位授权码

- **其他邮箱配置**
   - 请参考邮箱服务商的SMTP设置文档
   - 常见端口：465(SSL)或587(TLS)

## 高级配置

### 修改运行时间
编辑 `.github/workflows/daily_arxiv.yml`：
```yaml
on:
  schedule:
    - cron: '10 0 * * *'  # UTC时间，北京时间8:10
```

### 本地调试
```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试（需配置.env文件）
python arxiv_assistant.py
```

## 代码结构
```text
arxiv_assistant.py       # 主逻辑代码
.github/workflows/      # GitHub Actions配置
requirements.txt        # Python依赖
```

## 贡献指南
欢迎提交：
- 搜索语法增强
- 邮箱服务商配置模板
- 测试用例

## 许可证
[MIT License](LICENSE)
