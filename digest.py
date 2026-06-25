"""
Clinical Pharm Daily Digest
============================
1. collect -> 2. format -> 3. email
"""

import os
import sys
import base64
import smtplib
from email.utils import formatdate
from datetime import datetime

from collect import get_latest_articles
from config import LOOKBACK_DAYS


def _format_impact_badge(if_val):
    if if_val >= 50:
        return "[5*]"
    elif if_val >= 20:
        return "[4*]"
    elif if_val >= 10:
        return "[3*]"
    elif if_val >= 5:
        return "[2*]"
    elif if_val >= 3:
        return "[1*]"
    return ""


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
        badge = _format_impact_badge(a["impact_factor"])
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
            '<div style="display:flex;justify-content:space-between;">'
            f'<span style="background:#1a73e8;color:#fff;font-size:11px;'
            f'padding:3px 10px;border-radius:10px;">IF:{a["impact_factor"]:.1f}</span>'
            f'<span>{badge}</span></div>'
            f'<div style="font-size:13px;color:#555;">{a["journal"]}</div>'
            f'<h3 style="font-size:16px;"><a href="{a["url"]}" '
            f'style="color:#1a0dab;">{a["title"]}</a></h3>'
            f'<div style="font-size:12px;color:#777;">{authors_str}</div>'
            f'{pub_type_badges}'
            f'<div style="font-size:13px;color:#444;padding-top:8px;'
            f'border-top:1px solid #eee;">{abstract_short}</div>'
            f'<div style="font-size:12px;">{doi_link} '
            f'<span style="color:#999;">PMID:{a["pmid"]}</span></div></div>'
        )
        cards.append(card)

    articles_html = "\n".join(cards)
    no_articles = (
        '<div style="text-align:center;padding:40px;color:#888;">'
        'No new articles today</div>'
    )

    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '</head><body style="margin:0;padding:0;background:#f5f5f5;">'
        '<div style="max-width:640px;margin:0 auto;">'
        '<div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);'
        'padding:32px 20px;border-radius:0 0 24px 24px;color:#fff;text-align:center;">'
        '<h1 style="font-size:24px;">Clinical Pharm Daily Digest</h1>'
        f'<p style="font-size:14px;">{today_str}</p>'
        '<p style="font-size:13px;opacity:0.8;">High-Impact Journals</p></div>'
        '<div style="display:flex;justify-content:space-around;margin:20px 8px;'
        'background:#fff;border-radius:12px;padding:16px;">'
        f'<div style="text-align:center;"><div style="font-size:28px;font-weight:700;'
        f'color:#1a73e8;">{total}</div><div style="font-size:12px;color:#888;">Total</div></div>'
        f'<div style="text-align:center;"><div style="font-size:28px;font-weight:700;'
        f'color:#e67e22;">{if_ge_50}</div><div style="font-size:12px;color:#888;">IF>=50</div></div>'
        f'<div style="text-align:center;"><div style="font-size:28px;font-weight:700;'
        f'color:#27ae60;">{if_ge_20}</div><div style="font-size:12px;color:#888;">IF>=20</div></div>'
        f'</div><div style="padding:0 8px 20px;">'
        f'{articles_html if articles_html else no_articles}'
        f'</div><div style="text-align:center;padding:20px;font-size:11px;color:#aaa;">'
        f'<p>Source: PubMed (NCBI) · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'
        f'<p>Last {LOOKBACK_DAYS} days</p></div></div></body></html>'
    )
    return html


def build_text_digest(articles):
    lines = [
        "=" * 60,
        f"Clinical Pharm Daily Digest -- {datetime.now().strftime('%Y-%m-%d')}",
        "=" * 60,
        "",
    ]
    if not articles:
        lines.append("No new articles today.\n")
    for i, a in enumerate(articles, 1):
        badge = _format_impact_badge(a["impact_factor"])
        authors_str = _format_authors(a["authors"])
        lines.append(f"{'-' * 50}")
        lines.append(f"[{i}] {badge} IF: {a['impact_factor']:.1f}")
        lines.append(f"    Journal: {a['journal']}")
        lines.append(f"    Title: {a['title']}")
        lines.append(f"    Authors: {authors_str}")
        lines.append(f"    PMID: {a['pmid']}")
        if a.get("doi"):
            lines.append(f"    DOI: {a['doi']}")
        lines.append(f"    Link: {a['url']}")
        if a.get("abstract"):
            lines.append(f"    Abstract: {_truncate_abstract(a['abstract'], 200)}")
        lines.append("")
    lines.append("=" * 60)
    lines.append(f"Source: PubMed · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
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
        subject = f"[ClinicalPharm] Daily Digest {today_str}"

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
    print("Clinical Pharm Daily Digest - START")
    print("=" * 60)

    try:
        articles = get_latest_articles(debug_query=debug_query)
    except Exception as e:
        print(f"[error] collect failed: {e}")
        return 1

    if articles:
        print(f"[summary] {len(articles)} articles")
        hi = articles[0]["impact_factor"]
        lo = articles[-1]["impact_factor"]
        print(f"         IF range: {hi:.1f} - {lo:.1f}")
        for i, a in enumerate(articles[:5], 1):
            print(f"         {i}. [{a['impact_factor']:.1f}] {a['title'][:60]}...")
    else:
        print("[summary] no new articles")

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
        print("[send] sending email...")
        success = send_email(html_content, text_content)
        if success:
            print("[done] daily digest sent")
            return 0
        else:
            print("[fail] email send failed")
            return 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clinical Pharm Daily Digest")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--query", type=str, default=None)
    args = parser.parse_args()
    sys.exit(main(debug_query=args.query, dry_run=args.dry_run))
