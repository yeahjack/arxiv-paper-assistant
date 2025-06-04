# arxiv_assistant.py

import datetime
import email.utils
import os
import smtplib
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from tqdm import tqdm


def get_target_date(days_ago=2):
    today = datetime.datetime.now()
    target_date = today - datetime.timedelta(days=days_ago)
    return target_date.strftime("%Y-%m-%d")


def search_arxiv_papers(search_term, target_date, max_results=10):
    papers = []
    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query=all:{search_term}+AND+cat:cs.*&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    url = base_url + search_query

    headers = {"User-Agent": "Mozilla/5.0"}
    for attempt in range(10):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException as e:
            print(f"第 {attempt + 1} 次尝试失败: {e}")
            time.sleep(2)
    else:
        print("请求失败，请检查你的查询参数或网络连接。")
        return []

    root = ET.fromstring(response.content)
    namespaces = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    entries = root.findall(".//atom:entry", namespaces)
    if not entries:
        return []

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    target_date_obj = datetime.datetime.strptime(target_date, "%Y-%m-%d")
    today_obj = datetime.datetime.strptime(today_str, "%Y-%m-%d")

    for entry in entries:
        title = entry.find("./atom:title", namespaces).text.strip()
        summary = entry.find("./atom:summary", namespaces).text.strip()
        url = entry.find("./atom:id", namespaces).text.strip()
        pub_date_str = entry.find("./atom:published", namespaces).text
        pub_date = datetime.datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        pub_date_obj = datetime.datetime.strptime(pub_date, "%Y-%m-%d")
        authors = [a.find("./atom:name", namespaces).text.strip() for a in entry.findall("./atom:author", namespaces)]
        arxiv_id = url.split("/")[-1]
        categories = [c.get("term") for c in entry.findall("./atom:category", namespaces)]
        comments_elem = entry.find("./arxiv:comment", namespaces)
        comments = comments_elem.text.strip() if comments_elem is not None and comments_elem.text else None

        if target_date_obj <= pub_date_obj <= today_obj:
            papers.append(
                {
                    "title": title,
                    "authors": authors,
                    "url": url,
                    "arxiv_id": arxiv_id,
                    "pub_date": pub_date,
                    "summary": summary,
                    "categories": categories,
                    "comments": comments,
                }
            )

    print(f"找到 {len(papers)} 篇符合条件的论文。")

    return papers


def process_with_openai(text, prompt_template, openai_api_key, model_name="gpt-3.5-turbo", api_base=None):
    prompt = prompt_template.format(text=text)
    try:
        client_kwargs = {"api_key": openai_api_key}
        if api_base:
            client_kwargs["base_url"] = api_base
        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=model_name, messages=[{"role": "user", "content": prompt}], temperature=1.3, max_tokens=8192
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"处理文本时出现错误: {e}")
        return f"处理失败: {str(e)}"


def process_paper_with_openai(paper, translation_prompt, contribution_prompt, api_key, model, api_base):
    translated_summary = process_with_openai(paper["summary"], translation_prompt, api_key, model, api_base)
    contribution_summary = process_with_openai(paper["summary"], contribution_prompt, api_key, model, api_base)
    return (paper["arxiv_id"], translated_summary, contribution_summary)


def render_email_html(papers_by_keyword, keywords, today, date_range):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("email.html")
    return template.render(
        today=today,
        keywords=", ".join(keywords),
        date_range=date_range,
        keyword_papers=papers_by_keyword,
        total_papers=sum(len(p) for p in papers_by_keyword.values()),
    )


def send_email(
    subject,
    html_content,
    sender_email,
    sender_password,
    receiver_emails,
    sender_name=None,
    smtp_server="smtp.qq.com",
    smtp_port=465,
):
    message = MIMEMultipart("alternative")
    if sender_name:
        message["From"] = email.utils.formataddr((sender_name, sender_email))
    else:
        message["From"] = sender_email

    if isinstance(receiver_emails, list):
        message["To"] = ", ".join(receiver_emails)
        recipients = receiver_emails
    else:
        message["To"] = receiver_emails
        recipients = [receiver_emails]

    message["Subject"] = Header(subject, "utf-8")
    message.attach(MIMEText("请使用支持HTML的邮箱查看此内容。", "plain", "utf-8"))
    message.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, message.as_string())
        server.quit()
        print(f"邮件已成功发送至 {', '.join(recipients)}")
    except Exception as e:
        print(f"发送邮件时出现错误: {e}")


if __name__ == "__main__":
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
    SENDER_NAME = os.environ.get("SENDER_NAME", "arXiv论文助手")
    SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
    RECEIVER_EMAILS = os.environ.get("RECEIVER_EMAILS", "").split(",")
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.qq.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE")

    TRANSLATION_PROMPT = """我将给你一个人工智能领域的论文摘要，你需要翻译成中文，注意通顺流畅，领域专有用语（如transformer, token, logit）不用翻译。输出纯文本，不需要Markdown格式。\n{text}"""
    CONTRIBUTION_PROMPT = """我将给你一个人工智能领域的论文摘要，你需要使用中文，将最核心的内容用一句话说明，一般格式为：用了什么办法解决了什么问题。注意通顺流畅，领域专有用语（如transformer, token, logit）不用翻译。输出纯文本，不需要Markdown格式。\n{text}"""

    search_terms_str = os.environ.get("SEARCH_TERMS", '"transformer","large language model"')
    search_terms = [term.strip() for term in search_terms_str.split(",")]
    max_results = int(os.environ.get("MAX_RESULTS", "10"))
    days_ago = int(os.environ.get("DAYS_AGO", "2"))

    target_date = get_target_date(days_ago)
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")

    all_papers = {}
    keyword_papers = {}

    for search_term in tqdm(search_terms):
        papers = search_arxiv_papers(search_term, target_date, max_results)
        keyword_papers[search_term] = []
        for paper in papers:
            if paper["arxiv_id"] not in all_papers:
                all_papers[paper["arxiv_id"]] = paper
            keyword_papers[search_term].append(paper["arxiv_id"])

    if not all_papers:
        print("没有找到符合条件的论文。")
        exit()

    with ProcessPoolExecutor(max_workers=16) as executor:
        futures = [
            executor.submit(
                process_paper_with_openai,
                paper,
                TRANSLATION_PROMPT,
                CONTRIBUTION_PROMPT,
                OPENAI_API_KEY,
                OPENAI_MODEL,
                OPENAI_API_BASE,
            )
            for paper in all_papers.values()
        ]
        for future in futures:
            arxiv_id, translated, contribution = future.result()
            all_papers[arxiv_id]["translated_summary"] = translated
            all_papers[arxiv_id]["contribution"] = contribution

    papers_by_keyword = {}
    for keyword, arxiv_ids in keyword_papers.items():
        papers_by_keyword[keyword] = [
            {
                **all_papers[pid],
                "authors": ", ".join(all_papers[pid]["authors"]),
                "categories": ", ".join(all_papers[pid]["categories"]),
            }
            for pid in arxiv_ids
        ]

    html_content = render_email_html(papers_by_keyword, search_terms, today_date, f"{target_date} - {today_date}")

    send_email(
        f"arXiv论文日报 - {today_date} - {len(all_papers)}篇论文",
        html_content,
        SENDER_EMAIL,
        SENDER_PASSWORD,
        RECEIVER_EMAILS,
        SENDER_NAME,
        SMTP_SERVER,
        SMTP_PORT,
    )
