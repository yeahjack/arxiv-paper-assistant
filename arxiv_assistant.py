import requests
import datetime
import smtplib
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from openai import OpenAI
import xml.etree.ElementTree as ET
import os


def get_yesterday():
    """
    获取前一天的日期
    """
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def search_arxiv_papers(search_term, target_date, max_results=10):
    """
    在 arXiv 按照关键词查找特定日期的计算机科学（CS）领域论文，并提取标题、作者、摘要、分类和评论等信息
    """
    papers = []

    base_url = 'http://export.arxiv.org/api/query?'
    # 限定计算机科学领域
    search_query = f'search_query=all:{search_term}+AND+cat:cs.*&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending'
    response = requests.get(base_url + search_query)

    if response.status_code != 200:
        print("请求失败，请检查你的查询参数。")
        return []

    # 解析XML响应
    root = ET.fromstring(response.content)

    # 定义命名空间
    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }

    # 获取所有条目
    entries = root.findall('.//atom:entry', namespaces)

    if not entries:
        print("没有找到与搜索词匹配的论文。")
        return []

    for entry in entries:
        # 获取标题
        title = entry.find('./atom:title', namespaces).text.strip()

        # 获取摘要
        summary = entry.find('./atom:summary', namespaces).text.strip()

        # 获取链接
        url = entry.find('./atom:id', namespaces).text.strip()

        # 获取发布日期
        pub_date_str = entry.find('./atom:published', namespaces).text
        pub_date = datetime.datetime.strptime(
            pub_date_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

        # 获取作者
        authors = []
        for author in entry.findall('./atom:author', namespaces):
            author_name = author.find('./atom:name', namespaces).text.strip()
            authors.append(author_name)

        # 获取ArXiv ID
        arxiv_id = url.split('/')[-1]

        # 获取分类
        categories = []
        for category in entry.findall('./atom:category', namespaces):
            category_term = category.get('term')
            categories.append(category_term)

        # 获取评论 (comments)
        comments = None
        comments_elem = entry.find('./arxiv:comment', namespaces)
        if comments_elem is not None and comments_elem.text:
            comments = comments_elem.text.strip()

        # 判断文章的发布日期是否为目标日期
        if pub_date == target_date:
            papers.append({
                'title': title,
                'authors': authors,
                'url': url,
                'arxiv_id': arxiv_id,
                'pub_date': pub_date,
                'summary': summary,
                'categories': categories,
                'comments': comments,  # 添加评论字段
            })

    return papers


def process_with_openai(text, prompt_template, openai_api_key, model_name="gpt-3.5-turbo", api_base=None):
    """
    使用OpenAI处理文本（翻译或生成摘要）

    参数:
    text (str): 要处理的文本
    prompt_template (str): 提示词模板，将会把{text}替换为输入文本
    openai_api_key (str): OpenAI API密钥
    model_name (str): 使用的模型名称
    api_base (str, optional): 自定义API基础URL

    返回:
    str: 处理后的文本
    """
    # 构建prompt
    prompt = prompt_template.format(text=text)

    try:
        # 配置OpenAI客户端
        client_kwargs = {"api_key": openai_api_key}
        if api_base:
            client_kwargs["base_url"] = api_base

        client = OpenAI(**client_kwargs)

        # 调用API
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1.3,  # 使用相同的temperature值
            max_tokens=8192
        )

        # 提取结果
        result_text = response.choices[0].message.content.strip()
        return result_text
    except Exception as e:
        print(f"处理文本时出现错误: {e}")
        return f"处理失败: {str(e)}"


def format_paper_for_email(paper, translated_summary=None, contribution_summary=None):
    """
    格式化论文信息为邮件内容的一部分，使用简洁清晰的格式

    参数:
    paper (dict): 包含论文信息的字典
    translated_summary (str, optional): 翻译后的摘要
    contribution_summary (str, optional): 一句话贡献总结

    返回:
    str: 格式化后的论文信息
    """
    # 使用简单、清晰的分隔线
    separator = "----------------------------------------------------------------------\n"
    star_line = "*** "
    end_star_line = " ***"

    # 格式化作者列表
    authors_str = ", ".join(paper['authors'])

    # 格式化分类列表 - 添加错误处理
    categories_str = ", ".join(paper.get('categories', ["未知分类"]))

    # 构建格式化的论文信息
    paper_info = f"{separator}"
    paper_info += f"📄 标题: {paper['title']}\n"
    paper_info += f"👥 作者: {authors_str}\n"
    paper_info += f"🏷️ 分类: {categories_str}\n"
    paper_info += f"📅 发布日期: {paper['pub_date']}\n"

    # 添加评论信息 (如果有)
    if paper.get('comments'):
        paper_info += f"💬 评论: {paper['comments']}\n"

    paper_info += f"🔗 ArXiv链接: https://arxiv.org/abs/{paper['arxiv_id']}\n"
    paper_info += f"📄 PDF下载: https://arxiv.org/pdf/{paper['arxiv_id']}.pdf\n\n"

    # 如果有一句话贡献总结，添加到内容中
    if contribution_summary:
        paper_info += f"{star_line}贡献要点{end_star_line}\n"
        paper_info += f"{contribution_summary}\n\n"

    paper_info += f"{star_line}摘要{end_star_line}\n"
    paper_info += f"{paper['summary']}\n\n"

    # 如果有翻译的摘要，添加到内容中
    if translated_summary:
        paper_info += f"{star_line}中文摘要{end_star_line}\n"
        paper_info += f"{translated_summary}\n\n"

    paper_info += f"{separator}\n"

    return paper_info


def send_email(subject, content, sender_email, sender_password, receiver_emails, sender_name=None, smtp_server='smtp.qq.com', smtp_port=465):
    """
    通过邮件发送论文信息

    参数:
    subject (str): 邮件主题
    content (str): 邮件内容
    sender_email (str): 发件人邮箱地址
    sender_password (str): 发件人邮箱密码或应用专用密码
    receiver_emails (str or list): 收件人邮箱地址，可以是字符串或列表
    sender_name (str, optional): 发件人显示名称
    smtp_server (str): SMTP服务器地址
    smtp_port (int): SMTP服务器端口
    """
    # 创建邮件对象
    message = MIMEMultipart()

    # 设置发件人，使用email.utils格式化发件人地址
    if sender_name:
        message['From'] = email.utils.formataddr((sender_name, sender_email))
    else:
        message['From'] = sender_email

    # 处理收件人列表
    if isinstance(receiver_emails, list):
        message['To'] = ', '.join(receiver_emails)
        recipients = receiver_emails
    else:
        message['To'] = receiver_emails
        recipients = [receiver_emails]

    message['Subject'] = Header(subject, 'utf-8')

    # 添加邮件内容
    message.attach(MIMEText(content, 'plain', 'utf-8'))

    try:
        # 连接到SMTP服务器
        # 注意QQ邮箱使用SSL连接，所以使用SMTP_SSL而不是SMTP
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        # 不需要starttls，因为已经使用SSL连接
        server.login(sender_email, sender_password)

        # 发送邮件
        server.sendmail(sender_email, recipients, message.as_string())
        print(f"邮件已成功发送至 {', '.join(recipients)}")

        # 关闭连接
        server.quit()
    except Exception as e:
        print(f"发送邮件时出现错误: {e}")


if __name__ == '__main__':
    # 邮件设置
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
    SENDER_NAME = os.environ.get("SENDER_NAME", "ArXiv论文助手")
    SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
    RECEIVER_EMAILS = os.environ.get("RECEIVER_EMAILS", "").split(",")
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.qq.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))

    # OpenAI API设置
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "deepseek-chat")
    OPENAI_API_BASE = os.environ.get(
        "OPENAI_API_BASE", "https://api.deepseek.com/v1")

    # 定义提示词模板
    TRANSLATION_PROMPT = """我将给你一个人工智能领域的论文摘要，你需要翻译成中文，注意通顺流畅，领域专有用语（如transformer, token, logit）不用翻译。
{text}"""

    CONTRIBUTION_PROMPT = """我将给你一个人工智能领域的论文摘要，你需要使用中文，将最核心的内容用一句话说明，一般格式为：用了什么办法解决了什么问题。注意通顺流畅，领域专有用语（如transformer, token, logit）不用翻译。
{text}"""

    # 从环境变量获取关键词列表
    search_terms_str = os.environ.get(
        "SEARCH_TERMS", '"transformer","large language model"')
    search_terms = [term.strip()
                    for term in search_terms_str.strip('\'').split(',')]

    # 获取的最大论文数
    max_results = int(os.environ.get("MAX_RESULTS", "10"))

    # 获取前一天的日期
    yesterday = get_yesterday()

    # 用于存储不重复的论文（以arxiv_id为键）
    all_papers = {}
    # 用于存储每个关键词找到的论文ID列表
    keyword_papers = {}

    # 遍历每个关键词进行搜索
    for search_term in search_terms:
        print(f"搜索关键词 '{search_term}' 在 {yesterday} 发布的论文...")

        # 在 arxiv 按照关键词查找前一天的论文
        papers = search_arxiv_papers(search_term, yesterday, max_results)

        if not papers:
            print(f"没有找到{yesterday}发布的含 '{search_term}' 的论文")
            keyword_papers[search_term] = []
            continue

        print(f"找到 {len(papers)} 篇含 '{search_term}' 的论文")

        # 记录这个关键词找到的论文ID
        keyword_papers[search_term] = [paper['arxiv_id'] for paper in papers]

        # 将论文加入到总集合中（避免重复）
        for paper in papers:
            if paper['arxiv_id'] not in all_papers:
                all_papers[paper['arxiv_id']] = paper

    # 检查是否找到了任何论文
    if not all_papers:
        print(f"没有找到{yesterday}发布的符合任何关键词的论文，将发送空结果邮件")

        # 创建一个没有找到论文的邮件内容，使用简单格式
        email_content = f"""【ArXiv论文日报】{yesterday}
==================================================

📢 通知: 今日未找到符合以下关键词的论文:

"""
        # 添加所有搜索关键词，简单格式
        for search_term in search_terms:
            email_content += f"🔍 {search_term}\n"

        email_content += f"\n📋 我们将继续监控这些关键词，有新论文发布时会及时通知您。\n"
        email_content += f"==================================================\n"

        # 发送邮件
        send_email(
            f"ArXiv论文日报 - {yesterday} - 未找到相关论文",
            email_content,
            SENDER_EMAIL,
            SENDER_PASSWORD,
            RECEIVER_EMAILS,
            SENDER_NAME,
            SMTP_SERVER,
            SMTP_PORT
        )

        print("已发送空结果通知邮件")
        exit()

    print(f"总共找到 {len(all_papers)} 篇不重复的论文")

    # 创建一个简洁的邮件头部
    email_content = f"""【ArXiv论文日报】{yesterday} 关键词: {', '.join(search_terms)}
==================================================

📊 总览:
  • 总共找到 {len(all_papers)} 篇{yesterday}发布的相关论文

"""

    # 为每个关键词添加找到的论文数量
    for search_term in search_terms:
        papers_count = len(keyword_papers[search_term])
        if papers_count > 0:
            email_content += f"  • 关键词 {search_term}: {papers_count} 篇论文\n"

    email_content += f"==================================================\n\n"

    # 为每个关键词部分添加标题，使用简单清晰的格式
    for search_term in search_terms:
        paper_ids = keyword_papers[search_term]
        if not paper_ids:
            continue

        email_content += f"""
==================================================
🔎 关键词: {search_term} ({len(paper_ids)} 篇论文)
==================================================
"""

        # 处理这个关键词下的每篇论文
        for i, arxiv_id in enumerate(paper_ids, 1):
            paper = all_papers[arxiv_id]
            print(
                f"处理论文 {i}/{len(paper_ids)}: {paper['title']} (关键词: {search_term})")

            # 翻译摘要
            print(f"  - 翻译摘要...")
            translated_summary = process_with_openai(
                paper['summary'],
                TRANSLATION_PROMPT,
                OPENAI_API_KEY,
                OPENAI_MODEL,
                OPENAI_API_BASE
            )

            # 生成一句话贡献总结
            print(f"  - 生成贡献要点...")
            contribution_summary = process_with_openai(
                paper['summary'],
                CONTRIBUTION_PROMPT,
                OPENAI_API_KEY,
                OPENAI_MODEL,
                OPENAI_API_BASE
            )

            # 格式化论文信息并添加到邮件内容
            paper_section = format_paper_for_email(
                paper, translated_summary, contribution_summary)
            email_content += paper_section

    # 发送包含所有论文信息的邮件
    send_email(
        f"ArXiv论文日报 - {yesterday} - {len(all_papers)}篇论文",
        email_content,
        SENDER_EMAIL,
        SENDER_PASSWORD,
        RECEIVER_EMAILS,
        SENDER_NAME,
        SMTP_SERVER,
        SMTP_PORT
    )

    print(f"成功处理并发送了 {len(all_papers)} 篇论文的信息。")
