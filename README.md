# 📋 临床药理文献日报 · 自动推送系统

每日自动从 PubMed 采集高影响因子期刊上的临床药理学最新文献，
整理成精美摘要，通过邮件推送到你的手机。

---

## 系统架构

```
PubMed API (NCBI E-utilities)        ← 免费、开放、无需订阅
        ↓
  GitHub Actions (每日 UTC 23:00)     ← 免费云端定时运行
        ↓
    SMTP 邮件推送                    ← 发送到你的邮箱/手机邮箱
```

## 一键部署指南

### 第一步：Fork / Clone 本仓库

```bash
git clone https://github.com/YOUR_USER/clinical-pharmacy-digest.git
cd clinical-pharmacy-digest
```

或者直接在 GitHub 上 Fork 此仓库。

### 第二步：获取邮箱授权码

以 **QQ邮箱** 为例（推荐，国内用户最方便）：

1. 登录 QQ 邮箱 → 设置 → 账户
2. 找到 **"POP3/IMAP/SMTP服务"**
3. 开启 **"SMTP服务"**
4. 按提示发送短信，获取 **授权码**（16位字母，**不是你的QQ密码**）

> 163邮箱 / 126邮箱 / Outlook / Gmail 操作类似，都需要开启 SMTP 并获取授权码。

### 第三步：配置 GitHub Secrets

1. 在 GitHub 上打开你的仓库
2. 进入 **Settings → Secrets and variables → Actions**
3. 点击 **"New repository secret"**，依次添加以下 6 个密钥：

| Secret 名称 | 说明 | 示例值 |
|---|---|---|
| `SMTP_SERVER` | SMTP 服务器地址 | `smtp.qq.com` |
| `SMTP_PORT` | 端口（QQ邮箱用465） | `465` |
| `SMTP_USER` | 你的邮箱地址 | `yourname@qq.com` |
| `SMTP_PASS` | 邮箱授权码（**不是登录密码！**） | `abcdefghijklmnop` |
| `EMAIL_TO` | 接收摘要的目标邮箱 | `yourname@qq.com`（或手机邮箱） |
| `EMAIL_FROM_NAME` | 发件人显示名称 | `临床药理文献日报` |

**各邮箱 SMTP 配置参考：**

| 邮箱 | SMTP 服务器 | 端口 | 说明 |
|---|---|---|---|
| QQ邮箱 | `smtp.qq.com` | 465 | 需开启SMTP服务并获取授权码 |
| 163邮箱 | `smtp.163.com` | 465 | 同上 |
| Outlook | `smtp-mail.outlook.com` | 587 | 需开启SMTP并使用密码/应用密码 |
| Gmail | `smtp.gmail.com` | 587 | 需开启2FA并使用应用专用密码 |

**手机邮箱写法（让邮件直接变为手机短信/推送）：**

如果你想把摘要直接推送到手机，可以使用运营商的邮件网关：

| 运营商 | 手机邮箱格式 | 备注 |
|---|---|---|
| 中国移动 | `手机号@139.com` | 需在139邮箱App中开启邮件推送 |
| 中国联通 | `手机号@wo.cn` | 需开通联通手机邮箱 |
| 中国电信 | `手机号@189.cn` | 需开通189邮箱 |

> 📱 推荐直接用 QQ邮箱 App 或 网易邮箱大师 App 推送，体验更好。

### 第四步：启用 GitHub Actions

1. 在你的仓库中点击 **Actions** 标签
2. 左侧找到 **"每日临床药理文献摘要"**
3. 点击 **"Enable workflow"**
4. 你可以手动点击 **"Run workflow"** 测试一次

### 第五步：确认收到邮件 ✅

- 运行后等待约 1-2 分钟
- 检查你的邮箱（包括垃圾邮件箱）
- 如果收到邮件，配置完成！之后每天 07:00 自动推送

---

## 自定义配置

你可以根据自己的兴趣方向修改 `config.py`：

### 修改关注期刊

编辑 `HIGH_IMPACT_JOURNALS` 列表，添加或删除期刊：

```python
HIGH_IMPACT_JOURNALS = [
    ("The New England Journal of Medicine", 96.2),
    ("The Lancet", 80.2),
    # 添加你感兴趣的期刊...
]
```

### 修改检索关键词

编辑 `CLINICAL_PHARM_KEYWORDS` 列表：
- 使用 `[Majr]` 表示 MeSH 主要主题词（更精准）
- 使用 `[Title/Abstract]` 表示在标题/摘要中检索（更广泛）
- 使用 `[Journal]` 限定期刊名

### 修改时间范围

```python
LOOKBACK_DAYS = 3  # 改为 3 天回溯
```

### 修改推送时间

编辑 `.github/workflows/daily-digest.yml` 中的 cron 表达式：

```yaml
# 北京时间 08:00 → UTC 0:00
cron: '0 0 * * *'

# 北京时间 12:00 → UTC 4:00
cron: '0 4 * * *'

# 每个工作日早 07:00（周一至周五）
cron: '0 23 * * 0-5'
```

---

## PubMed 检索技巧

本系统使用 NCBI E-utilities API，检索语法与 PubMed 网站一致：

| 语法 | 含义 | 示例 |
|---|---|---|
| `[Majr]` | MeSH 主要主题词 | `Pharmacokinetics[Majr]` |
| `[Title/Abstract]` | 标题或摘要 | `PBPK[Title/Abstract]` |
| `[Journal]` | 限定期刊 | `"Lancet"[Journal]` |
| `AND` | 且 | `drug AND pharmacokinetics` |
| `OR` | 或 | `PKPD OR pharmacokinetic` |
| `"..."` | 精确短语 | `"therapeutic drug monitoring"` |

---

## 本地测试（可选）

如果你想先在本地运行测试：

```bash
cd clinical-pharmacy-digest

# 干运行模式（只打印摘要到控制台，不发送邮件）
python digest.py --dry-run

# 自定义检索式测试
python digest.py --dry-run --query '("Lancet"[Journal] OR "NEJM"[Journal]) AND pharmacokinetics[Title/Abstract] AND 2024[dp]'
```

本地运行无任何第三方依赖（全部使用 Python 标准库）。

---

## 常见问题

### Q: 收不到邮件？
A: 检查垃圾邮件箱；确认 Secrets 配置正确；QQ邮箱请确保使用的是**授权码**而非登录密码。

### Q: 搜索结果是空的？
A: 可能当天确实没有相关新文献（周末/节假日更新少），或者关键词太窄。可尝试增加 `LOOKBACK_DAYS` 或扩增关键词。

### Q: GitHub Actions 运行失败？
A: 在仓库 Actions 标签中查看具体错误日志。常见原因：Secrets 未配置、SMTP 连接超时（校园网环境不影响 GitHub 云端运行）、PubMed API 临时故障。

### Q: 我是校园网用户，能在本地跑吗？
A: 当然可以！校园网通常能直接访问 PubMed。在本地配置好邮箱环境变量后，用 Windows 任务计划程序设置定时任务即可。但推荐 GitHub Actions 方式——不用你的电脑开机。

---

## 隐私说明

- 本工具 **仅读取** PubMed 公开数据
- 邮箱凭据经过 GitHub Actions Secrets **加密存储**，不会泄露
- 不会收集或存储你的任何个人信息
- PubMed API 使用记录仅 NCBI 可见（标准日志）

---

## License

MIT
