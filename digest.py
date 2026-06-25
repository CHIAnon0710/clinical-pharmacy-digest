#!/usr/bin/env python3
"""
临床药理每日文献摘要 — 主入口
==============================
1. 采集 → 2. 格式化 → 3. 发送邮件
"""

import os
import sys
import base64
import smtplib
from email.utils import formatdate
from datetime import datetime
from typing import Optional

from collect import get_latest_articles
from config import LOOKBACK_DAYS


# ── 格式化 ──────────────────────────────────────────────────

def _format_impact_badge(if_val: float) -> str:
    """根据影响因子返回星级/等级标识"""
    if if_val >= 50:
        return "⭐⭐⭐⭐⭐"
    elif if_val >= 20:
        return "⭐⭐⭐⭐"
    elif if_val >= 10:
        return "⭐⭐⭐"
    elif if_val >= 5:
        return "⭐⭐"
    elif if_val >= 3:
        return "⭐"
    else:
        return ""


def _truncate_abstract(text: str, max_chars: int = 300) -> str:
    """截断摘要到指定长度"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def _format_authors(authors: list[str], max_count: int = 5) -> str:
    """格式化作者列表"""
    if not authors:
        return ""
    if len(authors) <= max_count:
        return ", ".join(authors)
    return ", ".join(authors[:max_count]) + f" et al."


def build_html_digest(articles: list[dict]) -> str:
    """构建 HTML 格式的每日摘要"""
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 统计信息
    total = len(articles)
    if_ge_50 = sum(1 for a in articles if a["impact_factor"] >= 50)
    if_ge_20 = sum(1 for a in articles if 20 <= a["impact_factor"] < 50)

    # 按 IF 分组展示
    def article_card(a: dict) -> str:
        badge = _format_impact_badge(a["impact_factor"])
        authors_str = _format_authors(a["authors"])
        abstract_short = _truncate_abstract(a["abstract"])

        # 文献类型标签
        pub_type_badges = ""
        for pt in a["pub_types"][:3]:
            pub_type_badges += f'<span style="display:inline-block;background:#e8f4f8;color:#2c7a9e;font-size:11px;padding:2px 8px;border-radius:10px;margin:2px 4px 2px 0;">{pt}</span>'

        # DOI 链接
        doi_link = ""
        if a.get("doi"):
            doi_link = f'<a href="https://doi.org/{a["doi"]}" style="color:#666;font-size:12px;">DOI</a>'

        return f"""
        <div style="background:#ffffff;border:1px solid #e0e0e0;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.08);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="background:#1a73e8;color:#ffffff;font-size:11px;font-weight:600;padding:3px 10px;border-radius:10px;">
                    IF: {a["impact_factor"]:.1f}
                </span>
                <span style="font-size:16px;">{badge}</span>
            </div>
            <div style="font-size:13px;color:#555;margin-bottom:6px;">
                {a["journal"]}
            </div>
            <h3 style="margin:0 0 8px;font-size:16px;line-height:1.4;">
                <a href="{a["url"]}" style="color:#1a0dab;text-decoration:none;">{a["title"]}</a>
            </h3>
            <div style="font-size:12px;color:#777;margin-bottom:8px;">
                {authors_str}
            </div>
            {pub_type_badges}
            <div style="font-size:13px;color:#444;line-height:1.5;margin-top:8px;padding-top:8px;border-top:1px solid #eee;">
                {abstract_short}
            </div>
            <div style="margin-top:8px;font-size:12px;">
                {doi_link}
                <span style="color:#999;margin-left:8px;">PMID: {a["pmid"]}</span>
            </div>
        </div>
        """

    articles_html = "\n".join(article_card(a) for a in articles)

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f5f5f5;">
    <div style="max-width:640px;margin:0 auto;padding:0;">

        <!-- 头部 -->
        <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:32px 20px;border-radius:0 0 24px 24px;color:#ffffff;text-align:center;">
            <h1 style="margin:0;font-size:24px;font-weight:700;">📋 临床药理文献日报</h1>
            <p style="margin:8px 0 0;font-size:14px;opacity:0.9;">{today_str}</p>
            <p style="margin:4px 0 0;font-size:13px;opacity:0.8;">高影响因子期刊 · 新近发表</p>
        </div>

        <!-- 统计条 -->
        <div style="display:flex;justify-content:space-around;margin:20px 8px;background:#ffffff;border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
            <div style="text-align:center;">
                <div style="font-size:28px;font-weight:700;color:#1a73e8;">{total}</div>
                <div style="font-size:12px;color:#888;">总文献</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:28px;font-weight:700;color:#e67e22;">{if_ge_50}</div>
                <div style="font-size:12px;color:#888;">IF≥50 顶刊</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:28px;font-weight:700;color:#27ae60;">{if_ge_20}</div>
                <div style="font-size:12px;color:#888;">IF≥20 权威</div>
            </div>
        </div>

        <!-- 文章列表 -->
        <div style="padding:0 8px 20px;">
            {articles_html if articles_html else '<div style="text-align:center;padding:40px 20px;color:#888;font-size:15px;">📭 今日无新文献<br><span style="font-size:13px;">可能是周末或节假日，文献更新较少</span></div>'}
        </div>

        <!-- 底部 -->
        <div style="text-align:center;padding:20px;font-size:11px;color:#aaa;">
            <p>数据来源：PubMed (NCBI) · 自动采集于 {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
            <p>涵盖近 {LOOKBACK_DAYS} 天发表的文章</p>
            <p style="margin-top:12px;">📧 每日自动推送 · 可随时退订</p>
        </div>
    </div>
</body>
</html>
    """
    return html


def build_text_digest(articles: list[dict]) -> str:
    """构建纯文本备用摘要"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"📋 临床药理文献日报 — {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("=" * 60)
    lines.append("")

    if not articles:
        lines.append("📭 今日无新文献。")
        lines.append("")

    for i, a in enumerate(articles, 1):
        badge = _format_impact_badge(a["impact_factor"])
        authors_str = _format_authors(a["authors"])
        lines.append(f"{'─' * 50}")
        lines.append(f"[{i}] {badge} IF: {a['impact_factor']:.1f}")
        lines.append(f"    期刊: {a['journal']}")
        lines.append(f"    标题: {a['title']}")
        lines.append(f"    作者: {authors_str}")
        lines.append(f"    PMID: {a['pmid']}")
        if a.get("doi"):
            lines.append(f"    DOI:  {a['doi']}")
        lines.append(f"    链接: {a['url']}")
        if a.get("abstract"):
            abstract_short = _truncate_abstract(a["abstract"], 200)
            lines.append(f"    摘要: {abstract_short}")
        lines.append("")

    lines.append("=" * 60)
    lines.append(f"数据来源：PubMed · 自动采集于 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return "\n".join(lines)


# ── 邮件发送 ────────────────────────────────────────────────

def _fold_base64(data: str) -> str:
    """将字符串做 base64 编码并按 76 字符分行"""
    encoded = base64.b64encode(data.encode("utf-8")).decode("ascii")
    return "\n".join(encoded[i:i + 76] for i in range(0, len(encoded), 76))


def send_email(html_content: str, text_content: str,
               subject: str = None) -> bool:
    """
    通过 SMTP 发送邮件 — 完全手写原始 MIME，不依赖 Python email 模块做头编码。
    QQ 邮箱 SMTP 对 From 头校验极端严格，必须极简格式。
    """
    smtp_server = os.environ.get("SMTP_SERVER", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    email_to = os.environ.get("EMAIL_TO", "")

    if not all([smtp_server, smtp_user, smtp_pass, email_to]):
        print("[邮件] ❌ 邮箱配置不完整，请检查环境变量")
        for k in ["SMTP_SERVER", "SMTP_USER", "SMTP_PASS", "EMAIL_TO"]:
            print(f"    {k}={'OK' if os.environ.get(k) else 'MISSING'}")
        return False

    today_str = datetime.now().strftime("%Y-%m-%d")
    if subject is None:
        subject = f"[ClinicalPharm] Daily Digest {today_str}"

    # —— 手写 MIME 原始字符串 ——
    domain = smtp_user.split("@")[-1] if "@" in smtp_user else "localhost"
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    boundary = f"==digest_{ts}=="

    text_b64 = _fold_base64(text_content)
    html_b64 = _fold_base64(html_content)

    raw = (
        f"From: {smtp_user}\r\n"
        f"To: {email_to}\r\n"
        f"Subject: {subject}\r\n"
        f"Date: {formatdate(localtime=True)}\r\n"
        f"Message-ID: <digest.{ts}@{domain}>\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: multipart/alternative; boundary=\"{boundary}\"\r\n"
        f"\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/plain; charset=\"utf-8\"\r\n"
        f"Content-Transfer-Encoding: base64\r\n"
        f"\r\n"
        f"{text_b64}\r\n"
        f"\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/html; charset=\"utf-8\"\r\n"
        f"Content-Transfer-Encoding: base64\r\n"
        f"\r\n"
        f"{html_b64}\r\n"
        f"\r\n"
        f"--{boundary}--"
    )

    # 打印原始邮件头用于调试
    header_only = "\n".join(raw.split("\r\n")[:12])
    print("[邮件] 前12行:")
    for line in header_only.split("\n"):
        print(f"  | {line}")

    try:
        print(f"[邮件] 正在连接 {smtp_server}:{smtp_port} ...")
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()

        # 打开 SMTP 调试，打印完整对话
        server.set_debuglevel(1)

        server.login(smtp_user, smtp_pass)
        # 显式编码为 ASCII bytes，彻底绕开 Python 的任何字符串处理
        raw_bytes = raw.encode("ascii")
        server.sendmail(smtp_user, [email_to], raw_bytes)
        server.quit()
        print(f"[邮件] ✅ 已发送至 {email_to}")
        return True
    except UnicodeError as e:
        print(f"[邮件] ❌ 编码错误 (消息含有非ASCII字符): {e}")
        return False
    except Exception as e:
        print(f"[邮件] ❌ 发送失败: {e}")
        return False


# ── 主流程 ──────────────────────────────────────────────────

def main(debug_query: str = None, dry_run: bool = False):
    """
    主入口。

    参数:
        debug_query: 可选的自定义检索式（调试用）
        dry_run:  True = 不发送邮件，仅打印摘要到控制台
    """
    print("=" * 60)
    print("📋 临床药理文献日报 — 开始采集")
    print("=" * 60)

    # 步骤 1: 采集
    print()
    try:
        articles = get_latest_articles(debug_query=debug_query)
    except Exception as e:
        print(f"[错误] 采集失败: {e}")
        return 1

    # 步骤 2: 格式化
    print()
    if articles:
        print(f"[摘要] 共 {len(articles)} 篇文献")
        print(f"       影响因子范围: {articles[0]['impact_factor']:.1f} — {articles[-1]['impact_factor']:.1f}")

        # 打印前几篇标题
        for i, a in enumerate(articles[:5], 1):
            print(f"       {i}. [{a['impact_factor']:.1f}] {a['title'][:60]}...")
    else:
        print("[摘要] 今日无新文献")
    print()

    # 步骤 3: 构建邮件
    html_content = build_html_digest(articles)
    text_content = build_text_digest(articles)

    # 步骤 4: 发送或打印
    if dry_run:
        print("=" * 60)
        print("📋 纯文本摘要预览（干运行模式）")
        print("=" * 60)
        print(text_content)
        print()
        print("=" * 60)
        print("HTML 长度: {} 字符".format(len(html_content)))
        print("=" * 60)
        return 0
    else:
        print("[发送] 正在发送邮件...")
        success = send_email(html_content, text_content)
        if success:
            print("[完成] ✅ 今日文献日报已发送")
            return 0
        else:
            print("[失败] ❌ 邮件发送失败")
            return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="临床药理每日文献摘要")
    parser.add_argument("--dry-run", action="store_true",
                        help="干运行：只打印摘要，不发送邮件")
    parser.add_argument("--query", type=str, default=None,
                        help="自定义 PubMed 检索式（调试用）")
    args = parser.parse_args()

    sys.exit(main(debug_query=args.query, dry_run=args.dry_run))
