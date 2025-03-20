# ArXiv 论文助手

ArXiv 论文助手是一个自动化工具，可以根据指定的关键词搜索 arXiv 上最新发布的论文，并通过邮件发送摘要和中文翻译。它使用 GitHub Actions 定时运行，无需服务器或本地环境。

## 核心功能

- 📝 **自动搜索** - 根据设定的关键词搜索 arXiv 上最新的论文
- 🌐 **智能翻译** - 使用 AI 服务将论文摘要翻译成中文
- 💡 **贡献总结** - 生成论文的一句话贡献要点
- 📧 **邮件推送** - 自动将论文信息以邮件形式发送到指定邮箱
- ⏰ **定时执行** - 利用 GitHub Actions 每天定时执行，无需手动操作

## 使用方法

### 1. 直接使用本仓库

1. **Fork 这个仓库**
   
   点击页面右上角的 "Fork" 按钮，将此仓库复制到您的 GitHub 账户下。

2. **设置 GitHub Secrets**

   在您 fork 的仓库中:
   - 进入 "Settings" > "Secrets and variables" > "Actions"
   - 点击 "New repository secret"
   - 添加以下 secrets:

   | 名称 | 说明 | 示例值 |
   |------|------|--------|
   | SENDER_EMAIL | 发件人邮箱 | your-email@example.com |
   | SENDER_NAME | 发件人名称 | ArXiv论文助手 |
   | SENDER_PASSWORD | 邮箱授权码（非登录密码） | abcdefghijklmnop |
   | RECEIVER_EMAILS | 收件人邮箱，多个用逗号分隔 | email1@example.com,email2@example.com |
   | SMTP_SERVER | SMTP 服务器地址 | smtp.example.com |
   | SMTP_PORT | SMTP 服务器端口 | 465 |
   | OPENAI_API_KEY | OpenAI 或其他兼容服务的 API 密钥 | sk-xxxxxxxxxxxxxxxx |
   | OPENAI_MODEL | 使用的 AI 模型 | `deepseek-chat` |
   | OPENAI_API_BASE | API 基础 URL（可选） | https://api.deepseek.com/v1 |
   | SEARCH_TERMS | 搜索关键词，用逗号分隔，每个关键词用引号包围 | `"transformer","large language model"` |
   | MAX_RESULTS | 每个关键词最多返回的论文数量 | 10 |

3. **测试工作流**

   - 进入仓库的 "Actions" 标签
   - 点击 "Daily ArXiv Paper Assistant" 工作流
   - 点击 "Run workflow" 下拉菜单，然后点击 "Run workflow" 按钮
   - 等待工作流运行完成，检查执行日志
   - 检查您的邮箱是否收到了邮件

### 2. 自定义配置

1. **修改搜索关键词**

   您可以随时更改搜索关键词，方法是:
   - 进入 "Settings" > "Secrets and variables" > "Actions"
   - 找到 "SEARCH_TERMS" 并点击 "Update"
   - 输入新的关键词列表，格式为: `"关键词1","关键词2","关键词3"`
   - 点击 "Update secret"

2. **调整运行时间**

   默认情况下，脚本会在每天北京时间 7:30 自动运行。如果您想修改运行时间:
   - 编辑 `.github/workflows/daily_arxiv.yml` 文件
   - 修改 `cron` 表达式 (默认是 `30 23 * * *`，对应北京时间 7:30)
   - 提交更改

   > 注意: cron 表达式使用 UTC 时间，北京时间 (UTC+8) 需要减去 8 小时

3. **调整翻译和摘要提示词**

   如果您想调整 AI 生成的翻译或摘要质量，可以修改 `arxiv_assistant.py` 文件中的提示词模板:
   ```python
   TRANSLATION_PROMPT = """..."""
   CONTRIBUTION_PROMPT = """..."""
   ```

### 3. 关于邮箱配置

对于 QQ 邮箱用户:
1. 登录 QQ 邮箱
2. 点击 "设置" > "账户" > "POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
3. 开启 "POP3/SMTP 服务"
4. 根据提示获取授权码
5. 使用该授权码作为 `SENDER_PASSWORD` 的值

其他邮箱服务请参考相应的官方文档获取 SMTP 服务配置和授权码。

## 常见问题

1. **GitHub Actions 没有运行**
   - 检查您是否正确设置了所有必需的 Secrets
   - 确认工作流文件 `.github/workflows/daily_arxiv.yml` 存在且格式正确
   - 检查 GitHub Actions 是否已在您的仓库中启用

2. **没有找到论文**
   - 可能当天确实没有与您的关键词匹配的新论文
   - 尝试调整搜索关键词或增加 `MAX_RESULTS` 的值

3. **邮件发送失败**
   - 确认 SMTP 服务器设置正确
   - 确认邮箱授权码有效
   - 查看工作流日志以获取详细错误信息

4. **翻译或摘要质量不佳**
   - 调整 `TRANSLATION_PROMPT` 和 `CONTRIBUTION_PROMPT` 中的提示词
   - 考虑更换 AI 模型

## 高级用法

### 本地调试

如果您想在本地运行此脚本进行调试:

1. 克隆仓库到本地
2. 创建一个 `.env` 文件，包含所有环境变量
3. 安装依赖: `pip install -r requirements.txt`
4. 运行脚本: `python arxiv_assistant.py`

### 自定义邮件格式

您可以通过修改 `format_paper_for_email()` 函数来自定义邮件格式。

## 贡献

欢迎提交 Issues 和 Pull Requests 来改进这个项目。

## 许可证

[MIT License](LICENSE)