# 生物医药校招情报库｜2026–2027 届

公开 GitHub 信息的可复现聚合工具。**不宣称岗位实时在招，也不猜测 HR 邮箱。**

## 运行方式

```bash
pip install -r requirements.txt
python scripts/collect.py
```

将项目上传到你自己的**公开 GitHub 仓库**，在 Actions 页手动执行 `Update biomed job index`；之后每周一自动执行（UTC 02:17，北京时间 10:17）。GitHub Actions 自带 `GITHUB_TOKEN`，无需额外申请个人 PAT。

- `data/biomed_announcements.csv`：实时采集后的公告级原始/去重记录，保留2026/2027届及历史截止时间。
- `data/company_channels.csv`：企业招聘入口（仅识别链接确实指向公开 ATS 的情况）。
- `data/verified_seed.csv`：人工核过 GitHub 原文的第一批历史样本，作为独立快照留档，**不是实时数据**。

## 来源与范围

**自动提取已适配：**

1. `oneetx-art/campus-announcements` 的医疗/医药/生物行业索引及公司公告文件（只收录明确 2026/2027 届、且公告学历包含硕士的招聘）。
2. `xixicc186/xixicc2027` 的 `jobs.json`（医疗医药相关、2026/2027届，学历不明独立标记为待核实）。

**其他待适配的数据源（不可将其算作已批量采集）：** `Zwondar/job-scraper`, `Bynlk/JobHunter`, `mengxi111/career-agent`, `namewyf/Campus2026`, `kknee-dev/recruit-hub`。这些有些是抓取工具或演示系统，**不能当成现成的完整招聘公告库**。

## 重要限制

- 一条公司校招公告可能代表多个岗位，公告写“硕士”不意味着每个岗位都招硕士。
- 不从毕业届别、GitHub 更新时间、首次观察日推断公告实际发布年份。
- 超期公告保留；“截止未公开”不等于“在招”。
- 邮箱仅限企业公开、明确用于招聘的邮箱，并且必须连同原始公告及用途一起核验记录。当前脚本**不抓取或臆造 HR 私人邮箱**。
- 仅使用公开访问的 GitHub 数据；不绕过登录、反爬或访问控制。
- 单次可能抓取数百公司 README；平台限流时会记录报错，本次导出可能不完整。可设置 `MAX_COMPANIES=100` 做小样本测试；默认 1200。
- 采集脚本尚未适配企业 Moka/北森公开职位 API：`company_channels.csv` 只是从已有公告中识别相关 URL。
