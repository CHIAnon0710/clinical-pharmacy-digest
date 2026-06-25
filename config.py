"""
临床药理每日文献摘要 - 配置文件
================================
在使用前，请填写下方邮箱配置（通过 GitHub Secrets 传入，不要写死密码）
"""

# ============================================================
# PubMed API 配置
# ============================================================

# NCBI API Key（可选，申请后可以提高频率限制 10次/秒）
# 申请地址：https://ncbi.nlm.nih.gov/account/
# 没有 API Key 也可以使用，限制为 3次/秒，对本脚本足够
# 也支持通过环境变量 NCBI_API_KEY 传入（GitHub Actions 中使用）
import os as _os
NCBI_API_KEY = _os.environ.get("NCBI_API_KEY", "")  # 留空也可用

# 每次检索最多返回的文章数
MAX_RESULTS = 20

# ============================================================
# 高影响因子期刊列表（临床药理相关）
# ============================================================
# 格式: (期刊全名, 影响因子)
# 影响因子为近似值，用于排序和标记
# 数据来源：Journal Citation Reports (JCR) 2024
HIGH_IMPACT_JOURNALS = [
    ("The New England Journal of Medicine", 96.2),
    ("The Lancet", 80.2),
    ("Nature Reviews Drug Discovery", 76.4),
    ("JAMA", 63.1),
    ("Nature Medicine", 58.7),
    ("The BMJ", 39.9),
    ("Journal of the American College of Cardiology", 24.0),
    ("European Heart Journal", 29.7),
    ("Circulation", 23.0),
    ("Gut", 19.8),
    ("Blood", 17.1),
    ("Annals of Internal Medicine", 19.6),
    ("The Lancet Neurology", 28.4),
    ("The Lancet Oncology", 33.1),
    ("The Lancet Diabetes & Endocrinology", 23.8),
    ("The Lancet Respiratory Medicine", 34.1),
    ("The Lancet Infectious Diseases", 25.4),
    ("The Lancet Global Health", 26.7),
    ("JAMA Internal Medicine", 22.6),
    ("JAMA Oncology", 24.8),
    ("JAMA Neurology", 19.0),
    ("JAMA Cardiology", 14.5),
    ("JAMA Pediatrics", 18.0),
    ("Clinical Pharmacology & Therapeutics", 7.6),
    ("Clinical Pharmacokinetics", 5.6),
    ("Pharmacological Reviews", 19.3),
    ("Trends in Pharmacological Sciences", 14.0),
    ("British Journal of Clinical Pharmacology", 3.9),
    ("Journal of Clinical Pharmacology", 2.9),
    ("European Journal of Clinical Pharmacology", 2.7),
    ("Pharmacotherapy", 4.4),
    ("Clinical Therapeutics", 3.5),
    ("CPT: Pharmacometrics & Systems Pharmacology", 3.5),
    ("Clinical and Translational Science", 3.6),
    ("Basic & Clinical Pharmacology & Toxicology", 2.7),
    ("The Journal of Clinical Pharmacology", 2.9),
    ("European Journal of Pharmaceutical Sciences", 4.3),
    ("International Journal of Pharmaceutics", 4.8),
    ("Pharmaceutics", 5.0),
    ("Journal of Pharmaceutical Sciences", 3.7),
    ("Drug Discovery Today", 7.4),
    ("Nature Reviews Clinical Oncology", 60.7),
    ("Alimentary Pharmacology & Therapeutics", 7.6),
    ("Journal of Antimicrobial Chemotherapy", 5.2),
    ("Antimicrobial Agents and Chemotherapy", 4.8),
    ("Diabetes Care", 14.8),
    ("Hypertension", 8.3),
    ("Stroke", 8.3),
    ("Chest", 9.1),
    ("Critical Care Medicine", 7.4),
]

# 构建期刊名称 → 影响因子 的映射
JOURNAL_IF_MAP = {j[0]: j[1] for j in HIGH_IMPACT_JOURNALS}

# ============================================================
# 检索关键词（覆盖临床药理学方向）
# ============================================================

# PubMed 检索的核心关键词（MeSH Terms + Text Words）
# 这些关键词会用 OR 连接
CLINICAL_PHARM_KEYWORDS = [
    # MeSH 主干
    "Clinical Pharmacology[Majr]",
    "Pharmacokinetics[Majr]",
    "Dose-Response Relationship, Drug[Majr]",
    "Drug Monitoring[Majr]",
    "Therapeutic Equivalency[Majr]",
    "Drug Interactions[Majr]",
    "Pharmacogenetics[Majr]",
    "Personalized Medicine[Majr]",
    "Drug Dosage Calculations[Majr]",

    # 文本词（覆盖最新文章还未标引 MeSH 的情况）
    "clinical pharmacokinetics[Title/Abstract]",
    "population pharmacokinetics[Title/Abstract]",
    "therapeutic drug monitoring[Title/Abstract]",
    "physiologically based pharmacokinetic[Title/Abstract]",
    "PBPK[Title/Abstract]",
    "pharmacodynamic[Title/Abstract]",
    "dose optimization[Title/Abstract]",
    "drug exposure[Title/Abstract]",
    "bioavailability[Title/Abstract]",
    "drug-drug interaction[Title/Abstract]",
]

# 额外的自由词（拓宽召回）
EXTRA_FREE_TEXT = [
    "pharmacokinetic",
    "PK/PD",
    "dosing regimen",
    "area under the curve",
    "AUC",
    "Cmax",
    "half-life",
    "clearance",
    "volume of distribution",
    "bioequivalence",
    "therapeutic range",
    "drug metabolism",
    "CYP450",
    "transporter",
]

# ============================================================
# 邮件配置（占位 — 真实值通过 GitHub Secrets 传入）
# ============================================================

# 发件邮箱配置（通过环境变量 / GitHub Secrets 设置）
# SMTP_SERVER: smtp.qq.com / smtp.163.com / smtp.gmail.com 等
# SMTP_PORT: 465 (SSL) 或 587 (TLS)
# SMTP_USER: 你的邮箱地址
# SMTP_PASS: 邮箱授权码（非登录密码！QQ邮箱需要开启SMTP并获取授权码）
# EMAIL_TO: 接收每日摘要的目标邮箱（可以是手机邮箱）
# EMAIL_FROM: 发件人名称，如 "临床药理文献日报"

# ============================================================
# 检索时间范围
# ============================================================
# 每次检索往回看的天数
LOOKBACK_DAYS = 2
