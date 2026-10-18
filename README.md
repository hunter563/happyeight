# 快乐8融合研究台 · HappyEight

把四个开源项目的核心函数接到同一份开奖数据、同一个网页和同一套滚动回测中。个人非商业研究项目。

**这不是四个网站的链接集合。** `fusion/engine.py` 和 `fusion/bridge.mjs` 会直接调用四个上游的代码，并输出统一结果。完整上游代码快照在 `vendor/`，版本记录见 [UPSTREAM_SOURCES.json](UPSTREAM_SOURCES.json)。原仓库自带依赖目录、编译产物和缓存不属于运行依赖。

## 已实现

- 统一数据：SQLite、CSV/JSON导入导出、每期20个不重复号码校验、去重、冲突整批回滚、来源记录。
- 在线同步：优先复用 gin-18 的汇鸟接口（自动分页），中彩网作为备用；增加超时、重试和数据校验，不可用时明确报错。
- 融合分析：KittenCN 特征分数、Luck8 日期加权频率、LuckyDD 频率/关联特征，固定等权融合；gin-18 提供独立号码计数与规则计算。
- 数据界面：最新开奖、历史记录、80号码频率/遗漏、区间/奇偶统计、各分支候选和随机对照。
- 滚动回测：逐期只使用此前的历史窗口；输出平均命中数、逐期结果、均匀随机对照和理论基线。
- 分析锁定：保存目标期号、截止期、输入数据指纹及各策略候选；导入对应开奖结果后自动复盘。
- 规则计算：调用 gin-18 的组合和参考奖金函数；额外计算超几何理论命中分布，浮动奖金不当作固定收益。

## 四项目如何融合

| 上游 | 直接调用的模块 | 在融合版中的职责 |
|---|---|---|
| [KittenCN/kl8-lottery-analyzer](https://github.com/KittenCN/kl8-lottery-analyzer) | `compute_enhanced_scores` | 近期动量、共现谱与Dirichlet平滑特征 |
| [fightingfor/Luck8](https://github.com/fightingfor/Luck8) | `KL8Predictor.analyze_frequency` | 按真实开奖日期加权的历史频率 |
| [FanKang2021/LuckyDD](https://github.com/FanKang2021/LuckyDD) | `calculateHotColdNumbers`、`calculateMissingNumbers`、`findNumberCorrelations` 等 | 统计、遗漏、区间、奇偶及关联特征 |
| [gin-18/lottery](https://github.com/gin-18/lottery) | `countNumberInData`、`combine`、`calculateRegularPrizeCounts` 等 | 号码计数、组合与规则计算 |

其中 gin-18 是统计/工具项目，本身不提供预测器。融合版没有把它虚构为“第四个AI模型”。三个分析分支归一化后固定等权，分数只用于排序，不是中奖概率。

## 本机启动

需要 **Python 3.11–3.13 和 Node.js 24**。无须 API Key、云服务器或 Supabase。

```bash
python -m venv .venv
# Windows 激活：.venv\Scripts\activate
# macOS/Linux 激活：source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

打开 **http://127.0.0.1:8768**。Windows 安装好 Python 和 Node.js 后，也可双击 `start.bat`。

默认仅监听本机。`--port` 可改端口，`--database` 可改数据库路径，`--no-seed` 可跳过内置数据。`KL8_NODE` 可指定 Node.js 路径。

## 云端个人试用

仓库包含 Dockerfile 与 Railway 配置，可部署完整 Python/Node 分析引擎。设置 `KL8_ACCESS_PASSWORD`（至少16字符），用户名默认为 `happy8`，可用 `KL8_ACCESS_USERNAME` 修改。只通过 HTTPS 访问，浏览器会提示输入账号密码。密码存于部署环境变量，不能提交到仓库。

容器默认开启 `KL8_REQUIRE_AUTH=1`，未配置足够长度的密码会拒绝启动。所有页面、静态资源和数据接口均受认证保护，仅 `/api/health` 返回不含数据的健康状态。未设置密码的本机启动方式保持不变。

挂载持久化卷至 `/data`，数据库位于 `/data/fusion.sqlite`，重启和更新后保留导入数据及锁定记录。此版本用于单人试用，不提供多个用户的数据隔离。建议单实例、1GB内存；空闲时可在 Railway 开启休眠。

## 数据与验证边界

首次启动导入并合并 **2,097期历史快照，2020001至2026276，截止2026-10-17**：Luck8 自带的1,545期旧数据，加上 `samples/history-snapshot.json` 中从汇鸟接口取得的近1,000期数据，按期号去重。近1,000期号码已与500走势图逐期交叉核对一致；这不等于逐期官方认证。页面明确展示截止日期和数据来源。可以在线同步或导入新的CSV/JSON。

CSV支持 `issue,date,numbers` 或 `期号,开奖日期,开奖号码`。号码列用双引号包住以逗号分隔的20个号码。导出的JSON可再次导入。

“锁定”表示相对于**当前库内**尚未导入的期号冻结分析，不能证明提交早于真实开奖时间。正式前瞻验证前必须先更新数据，并在真实开奖前锁定。数据库是本机文件，可被机主修改，不是第三方公证系统。

奖金规则沿用 gin-18 快照，**未核验当前官方版本**，仅用于规则演示。未根据原项目的“推荐”“置信度”文案声称预测有效。

## 修正和隔离

1. LuckyDD 原推荐接口给评分增加随机数，融合版不调用该接口，也不把评分显示成准确率。
2. LuckyDD 原遗漏计数存在最新命中为1、从未出现为0的问题，适配层统一为0和窗口长度。
3. Luck8 原期望值函数拿同一期号码子集和自身计算命中，存在目标泄露；该函数与旧奖金表不参与融合。
4. KittenCN 外部图嵌入缓存可能包含窗口外数据，默认禁用；PCA、遗传算法、Copula、FP-Growth完整候选生成链仍保存在上游源码中，本版没有声称已接入所有实验功能。
5. 移除 Luck8 抓取脚本中的上游硬编码会话Cookie，融合采集器不依赖私人登录信息。

## 测试

```bash
python -m unittest discover -s tests -v
```

覆盖真实上游函数调用、重复/冲突导入、遗漏边界、理论概率、组合计算、时间隔离、锁定复盘和HTTP接口。持续集成配置见 `.github/workflows/ci.yml`。验证记录见 [docs/VALIDATION.md](docs/VALIDATION.md)。

## 使用限制与归属

仅供个人非商业研究；保留所有上游归属和条款，不对四个项目统一改授许可证。LuckyDD 的 README 明确禁止商业用途。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

本项目未证明任何策略能长期优于随机选号，也未验证盈利能力。
