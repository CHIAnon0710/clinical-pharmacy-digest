"""
PubMed 文献采集模块
===================
通过 NCBI E-utilities API 检索和获取文献详情。
"""

import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from config import (
    NCBI_API_KEY,
    MAX_RESULTS,
    CLINICAL_PHARM_KEYWORDS,
    EXTRA_FREE_TEXT,
    JOURNAL_IF_MAP,
    LOOKBACK_DAYS,
)

# NCBI E-utilities 基础 URL
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# 请求之间的最小间隔（秒）— 遵守 NCBI 频率限制
MIN_INTERVAL = 0.35  # 无 API Key 时 < 3次/秒


def _rate_limited_request(url: str) -> str:
    """带频率限制的 HTTP GET 请求"""
    time.sleep(MIN_INTERVAL)
    req = Request(url)
    # 设置 User-Agent 是 NCBI 推荐的做法
    req.add_header("User-Agent", "ClinicalPharmDigest/1.0")
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


# ── 发表日期计算 ──────────────────────────────────────────

def _get_date_range() -> tuple[str, str]:
    """获取检索日期范围：最近 LOOKBACK_DAYS 天"""
    today = datetime.now()
    start = today - timedelta(days=LOOKBACK_DAYS)
    return (start.strftime("%Y/%m/%d"), today.strftime("%Y/%m/%d"))


# ── PubMed 检索 ──────────────────────────────────────────

def _build_query() -> str:
    """
    构建 PubMed 检索查询。
    策略：高 IF 期刊作为强制限定，加上临床药理关键词。
    """
    # 高 IF 期刊的完整名称（用 OR 连接）
    journal_names = list(JOURNAL_IF_MAP.keys())
    journal_query = " OR ".join(
        [f'"{name}"[Journal]' for name in journal_names]
    )
    journal_query = f"({journal_query})"

    # 关键词查询（OR 连接所有）
    keyword_query = " OR ".join(CLINICAL_PHARM_KEYWORDS)
    free_text = " OR ".join(f"{kw}[Title/Abstract]" for kw in EXTRA_FREE_TEXT)
    full_keyword = f"({keyword_query} OR {free_text})"

    # 日期范围
    date_from, date_to = _get_date_range()
    date_filter = f'("{date_from}"[Date - Publication] : "{date_to}"[Date - Publication])'

    # 最终查询：期刊限定 AND 关键词 AND 最近日期
    query = f"{journal_query} AND {full_keyword} AND {date_filter}"

    return query


def search_pubmed(query: str = None, max_results: int = MAX_RESULTS) -> list[str]:
    """
    搜索 PubMed，返回 PMID 列表。

    参数:
        query: PubMed 检索式，None 则使用默认构建的检索式
        max_results: 最大返回数量

    返回:
        PMID 字符串列表
    """
    if query is None:
        query = _build_query()

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "date",  # 按出版日期排序（最新的在前）
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    url = BASE_URL + "esearch.fcgi?" + urlencode(params)
    data = _rate_limited_request(url)

    # 解析 JSON 响应
    result = json.loads(data)
    id_list = result.get("esearchresult", {}).get("idlist", [])

    return id_list


# ── 文献详情获取 ──────────────────────────────────────────

def _safe_text(element: Optional[ET.Element], default: str = "") -> str:
    """安全提取 XML 元素的纯文本内容（含子标签中的文字）"""
    if element is None:
        return default
    # itertext() 获取所有文本节点（包括子标签如 <i>CYP3A4</i> 中的文字）
    parts = [t for t in element.itertext() if t]
    text = "".join(parts).strip()
    return text if text else default


def _safe_attr(element: Optional[ET.Element], attr: str, default: str = "") -> str:
    """安全提取 XML 元素的属性值"""
    if element is not None:
        val = element.get(attr)
        if val:
            return val.strip()
    return default


def _extract_authors(article_el: ET.Element) -> list[str]:
    """提取作者列表"""
    authors = []
    author_list = article_el.find(".//AuthorList")
    if author_list is None:
        return authors

    for author in author_list.findall("Author"):
        last = _safe_text(author.find("LastName"))
        fore = _safe_text(author.find("ForeName"))
        if last or fore:
            # 缩写形式: Smith J
            initials = ""
            if fore:
                initials = "".join(
                    [w[0] for w in fore.split() if w[0].isalpha()]
                )
            name = f"{last} {initials}" if initials else last
            authors.append(name)

    return authors


def _extract_journal_info(article_el: ET.Element) -> tuple[str, float]:
    """
    提取期刊名称和影响因子。
    返回 (journal_name, impact_factor)
    """
    journal = article_el.find(".//Journal/Title")
    journal_name = _safe_text(journal)

    # 通过期刊名查找影响因子（近似匹配）
    if journal_name:
        # 精确匹配
        if journal_name in JOURNAL_IF_MAP:
            return journal_name, JOURNAL_IF_MAP[journal_name]
        # 模糊匹配（有些期刊名在 PubMed 中略有不同）
        for key, if_val in JOURNAL_IF_MAP.items():
            if key.lower() in journal_name.lower() or journal_name.lower() in key.lower():
                return journal_name, if_val

    return journal_name, 0.0


def _extract_doi(article_el: ET.Element) -> str:
    """提取 DOI"""
    # 从 ELocationID 中找（优先，通常在 Article 一级）
    for eid in article_el.findall(".//ELocationID"):
        if eid.get("EIdType") == "doi":
            return _safe_text(eid)
    # 从 ArticleIdList 中找（通常在 PubmedData 一级）
    for aid in article_el.findall(".//ArticleId"):
        if aid.get("IdType") == "doi":
            return _safe_text(aid)
    return ""


def _extract_abstract(article_el: ET.Element) -> str:
    """
    提取摘要文本。
    注意：NCBI XML 中 AbstractText 的 Label 是属性，不是子元素。
    """
    abstract_el = article_el.find(".//Abstract")
    if abstract_el is None:
        return ""

    parts = []
    for child in abstract_el:
        label = _safe_attr(child, "Label")  # Label 是属性而非子元素！
        text = _safe_text(child)
        if label and text:
            parts.append(f"[{label}] {text}")
        elif text:
            parts.append(text)

    return " ".join(parts)


def _extract_publication_types(article_el: ET.Element) -> list[str]:
    """提取文献类型（Randomized Controlled Trial, Review, etc.）"""
    types = []
    for pt in article_el.findall(".//PublicationType"):
        t = _safe_text(pt)
        if t:
            types.append(t)
    return types


def fetch_details(pmids: list[str]) -> list[dict]:
    """
    根据 PMID 列表获取文献详细信息。

    返回:
        字典列表，每个字典包含:
        - pmid, title, authors, journal, impact_factor,
          doi, pub_date, abstract, pub_types, url
    """
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    url = BASE_URL + "efetch.fcgi?" + urlencode(params)
    xml_data = _rate_limited_request(url)

    root = ET.fromstring(xml_data)
    articles = []

    for article_el in root.findall(".//PubmedArticle"):
        medline = article_el.find(".//MedlineCitation")
        article = medline.find(".//Article") if medline is not None else None
        if article is None:
            continue

        pmid = _safe_text(medline.find(".//PMID"))
        title = _safe_text(article.find("ArticleTitle"))
        authors = _extract_authors(article)
        journal_name, impact_factor = _extract_journal_info(article)
        doi = _extract_doi(article)
        abstract = _extract_abstract(article)
        pub_types = _extract_publication_types(article)

        # 获取出版年份
        year_el = article.find(".//Journal/JournalIssue/PubDate/Year")
        pub_date = _safe_text(year_el)

        # 构建 PubMed URL
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        articles.append({
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "journal": journal_name,
            "impact_factor": impact_factor,
            "doi": doi,
            "pub_date": pub_date,
            "abstract": abstract,
            "pub_types": pub_types,
            "url": pubmed_url,
        })

    return articles


# ── 综合调用 ─────────────────────────────────────────────

def get_latest_articles(debug_query: str = None) -> list[dict]:
    """
    一站式获取近期高影响因子期刊上的临床药理相关文献。

    参数:
        debug_query: 可选的调试用检索式（不传则自动构建）

    返回:
        按影响因子降序排列的文献列表
    """
    print(f"[采集] 构建检索式并搜索 PubMed...")
    if debug_query:
        query = debug_query
        print(f"[采集] 使用自定义检索式: {query}")
    else:
        query = _build_query()
        print(f"[采集] 自动构建的检索式已生成")

    pmids = search_pubmed(query=query)

    if not pmids:
        print("[采集] 未检索到文献")
        return []

    print(f"[采集] 检索到 {len(pmids)} 篇文献，获取详细信息...")
    articles = fetch_details(pmids)

    # 按影响因子降序排列
    articles.sort(key=lambda a: a["impact_factor"], reverse=True)

    return articles
