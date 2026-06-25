"""
Clinical Pharm Daily Digest / 临床药理文献日报
================================================
1. collect / 采集 -> 2. format / 格式化 -> 3. email / 发送邮件
"""

import os
import sys
import base64
import smtplib
from email.utils import formatdate
from datetime import datetime

from collect import get_latest_articles
from config import LOOKBACK_DAYS


def _impact_level(if_val):
    if if_val >= 50:
        return "SSS", "顶刊"
    elif if_val >= 20:
        return "SS", "权威"
    elif if_val >= 10:
        return "S", "一流"
    elif if_val >= 5:
        return "A", "优秀"
    elif if_val >= 3:
        return "B", "良好"
    return "", ""


def _truncate_abstract(text, max_chars=300):
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def _format_authors(authors, max_count=5):
    if not authors:
        return ""
    if len(authors) <= max_count:
        return ", ".join(authors)
    return ", ".join(authors[:max_count]) + " et al."


def build_html_digest(articles):
    today_str = datetime.now().strftime("%Y-%m-%d")
    total = len(articles)
    if_ge_50 = sum(1 for a in articles if a["impact_factor"] >= 50)
    if_ge_20 = sum(1 for a in articles if 20 <= a["impact_factor"] < 50)

    cards = []
    for a in articles:
        tier, tier_cn = _impact_level(a["impact_factor"])
        authors_str = _format_authors(a["authors"])
        abstract_short = _truncate_abstract(a["abstract"])

        pub_type_badges = ""
        for pt in a["pub_types"][:3]:
            pub_type_badges += (
                '<span style="display:inline-block;background:#e8f4f8;'
                'color:#2c7a9e;font-size:11px;padding:2px 8px;'
                f'border-radius:10px;margin:2px 4px 2px 0;">{pt}</span>'
            )
        doi_link = ""
        if a.get("doi"):
            doi_link = (
                f'<a href="https://doi.org/{a["doi"]}" '
                f'style="color:#666;font-size:12px;">DOI</a>'
            )
        card = (
            '<div style="background:#fff;border:1px solid #e0e0e0;'
            'border-radius:12px;padding:16px;margin-bottom:16px;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="background:#1a73e8;color:#fff;font-size:11px;'
            f'padding:3px 10px;border-radius:10px;">IF {a["impact_factor"]:.1f}</span>'
            f'<span style="font-size:14px;color:#e67e22;">{tier} {tier_cn}</span></div>'
            f'<div style="font-size:13px;color:#555;margin-top:8px;">{a["journal"]}</div>'
            f'<h3 style="font-size:16px;margin:8px 0;"><a href="{a["url"]}" '
            f'style="color:#1a0dab;text-decoration:none;">{a["title"]}</a></h3>'
            f'<div style="font-size:12px;color:#777;">{authors_str}</div>'
            f'<div style="margin:8px 0;">{pub_type_badges}</div>'
            f'<div style="font-size:13px;color:#444;padding-top:8px;'
            f'border-top:1px solid #eee;">{abstract_short}</div>'
            f'<div style="font-size:12px;margin-top:6px;">{doi_link} '
            f'<span style="color:#999;">PMID: {a["pmid"]}</span></div></div>'
        )
        cards.append(card)

    articles_html = "\n".join(cards)
    no_articles = (
        '<div style="text-align:center;padding:40px;color:#888;font-size:15px;">'
        'No new articles today / 今日暂无新文献<br>'
        '<span style="font-size:13px;">(周末或节假日更新较少)</span></div>'
    )

    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '</head><body style="margin:0;padding:0;background:#f5f5f5;">'
        '<div style="max-width:640px;margin:0 auto;">'

        # Header
        '<div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);'
        'padding:32px 20px;border-radius:0 0 24px 24px;color:#fff;text-align:center;">'
        '<h1 style="font-size:24px;margin:0;">Clinical Pharm Daily Digest</h1>'
        '<h2 style="font-size:20px;margin:4px 0;font-weight:400;">临床药理文献日报</h2>'
        f'<p style="font-size:14px;opacity:0.9;margin:12px 0 4px;">{today_str}</p>'
        '<p style="font-size:13px;opacity:0.8;margin:2px 0;">'
        'High-Impact Journals · Latest Articles</p>'
        '<p style="font-size:13px;opacity:0.8;margin:2px 0;">'
        '高影响因子期刊 · 新近发表</p></div>'

        # Stats
        '<div style="display:flex;justify-content:space-around;margin:20px 8px;'
        'background:#fff;border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
        f'<div style="text-align:center;"><div style="font-size:28px;font-weight:700;'
        f'color:#1a73e8;">{total}</div><div style="font-size:12px;color:#888;">'
        f'总文献<br>Total</div></div>'
        f'<div style="text-align:center;"><div style="font-size:28px;font-weight:700;'
        f'color:#e67e22;">{if_ge_50}</div><div style="font-size:12px;color:#888;">'
        f'IF &ge; 50<br>顶刊</div></div>'
        f'<div style="text-align:center;"><div style="font-size:28px;font-weight:700;'
        f'color:#27ae60;">{if_ge_20}</div><div style="font-size:12px;color:#888;">'
        f'IF &ge; 20<br>权威</div></div>'
        '</div>'

        # Articles
        f'<div style="padding:0 8px 20px;">'
        f'{articles_html if articles_html else no_articles}</div>'

        # Footer
        '<div style="text-align:center;padding:20px;font-size:11px;color:#aaa;">'
        f'<p>Source: PubMed (NCBI) · Generated at {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC</p>'
        f'<p>数据来源：PubMed (NCBI) · 涵盖近 {LOOKBACK_DAYS} 天发表的文章</p>'
        '<p style="margin-top:12px;">Daily Auto Digest / 每日自动推送</p>'
        '<p style="font-size:10px;">Clinical Pharm Digest v1.0</p></div>'
        '</div></body></html>'
    )
    return html


def build_text_digest(articles):
    lines = [
        "=" * 60,
        "  Clinical Pharm Daily Digest / 临床药理文献日报",
        f"  {datetime.now().strftime('%Y-%m-%d')}",
        "=" * 60,
        "",
    ]
    if not articles:
        lines.append("  No new articles today / 今日暂无新文献\n")
    for i, a in enumerate(articles, 1):
        tier, tier_cn = _impact_level(a["impact_factor"])
        authors_str = _format_authors(a["authors"])
        lines.append(f"{'-' * 50}")
        lines.append(f"  [{i}] {tier} {tier_cn}  |  IF: {a['impact_factor']:.1f}")
        lines.append(f"  Journal / 期刊 : {a['journal']}")
        lines.append(f"  Title  / 标题  : {a['title']}")
        lines.append(f"  Authors/ 作者  : {authors_str}")
        lines.append(f"  PMID   : {a['pmid']}")
        if a.get("doi"):
            lines.append(f"  DOI    : {a['doi']}")
        lines.append(f"  Link   : {a['url']}")
        if a.get("abstract"):
            lines.append(f"  Abstract: {_truncate_abstract(a['abstract'], 200)}")
        lines.append("")
    lines.append("=" * 60)
    lines.append(f"  PubMed (NCBI) · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("  Clinical Pharm Digest v1.0")
    return "\n".join(lines)


def _fold_base64(data):
    encoded = base64.b64encode(data.encode("utf-8")).decode("ascii")
    return "\n".join(encoded[i:i + 76] for i in range(0, len(encoded), 76))


def send_email(html_content, text_content, subject=None):
    smtp_server = os.environ.get("SMTP_SERVER", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "465").strip())
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    email_to = os.environ.get("EMAIL_TO", "").strip()

    if not all([smtp_server, smtp_user, smtp_pass, email_to]):
        print("[mail] missing secrets")
        return False

    today_str = datetime.now().strftime("%Y-%m-%d")
    if subject is None:
        subject = f"[ClinicalPharm] Daily Digest / 临床药理日报 {today_str}"

    # RFC2047 encode Subject (required for non-ASCII chars in email headers)
    subject_encoded = base64.b64encode(subject.encode("utf-8")).decode("ascii")
    subject_header = f"=?utf-8?B?{subject_encoded}?="

    domain = smtp_user.split("@")[-1] if "@" in smtp_user else "localhost"
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    boundary = f"==digest_{ts}=="

    text_b64 = _fold_base64(text_content)
    html_b64 = _fold_base64(html_content)

    raw = (
        f"From: {smtp_user}\r\n"
        f"To: {email_to}\r\n"
        f"Subject: {subject_header}\r\n"
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

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [email_to], raw.encode("ascii"))
        server.quit()
        print("[mail] sent OK")
        return True
    except Exception as e:
        print(f"[mail] send failed: {e}")
        return False


def main(debug_query=None, dry_run=False):
    print("=" * 60)
    print("Clinical Pharm Daily Digest / 临床药理文献日报")
    print("=" * 60)

    try:
        articles = get_latest_articles(debug_query=debug_query)
    except Exception as e:
        print(f"[error] collect failed: {e}")
        return 1

    if articles:
        print(f"[summary] {len(articles)} articles / 篇文献")
        hi = articles[0]["impact_factor"]
        lo = articles[-1]["impact_factor"]
        print(f"         IF range: {hi:.1f} - {lo:.1f}")
        for i, a in enumerate(articles[:5], 1):
            print(f"         {i}. [{a['impact_factor']:.1f}] {a['title'][:60]}...")
    else:
        print("[summary] no new articles / 无新文献")

    html_content = build_html_digest(articles)
    text_content = build_text_digest(articles)

    if dry_run:
        print("=" * 60)
        print("TEXT PREVIEW (dry-run)")
        print("=" * 60)
        print(text_content)
        print(f"HTML length: {len(html_content)} chars")
        return 0
    else:
        print("[send] sending email / 正在发送...")
        success = send_email(html_content, text_content)
        if success:
            print("[done] daily digest sent / 日报已发送")
            return 0
        else:
            print("[fail] email send failed / 发送失败")
            return 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="临床药理文献日报")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--query", type=str, default=None)
    args = parser.parse_args()
    sys.exit(main(debug_query=args.query, dry_run=args.dry_run))
