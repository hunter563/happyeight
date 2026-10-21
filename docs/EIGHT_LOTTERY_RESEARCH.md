# 八彩分析首版：公开功能反查与实现记录

反查日期：2026-10-21。范围固定为双色球、福彩3D、快乐8、七乐彩、大乐透、排列3、排列5、七星彩。功能参考仅使用图感觉、乐彩网；号码规则使用福彩、体彩公开规则交叉核对。

这是第一批可运行的历史分析功能，不代表两个站点的所有图表已1:1复刻或逐项验收。此批不涉及竞彩、每日一卦、收费会员、原生安装包或服务器迁移。

## 公开目录与号码模型

| 彩种 / API代码 | 图感觉目录 | 乐彩网目录 | 本次实现的号码模型 |
|---|---|---|---|
| 双色球 `ssq` | [目录](https://tb.tuganjue.com/i-l-ssq.html) | [目录](https://www.17500.cn/chart/index-1-ssq.html) | 红球6个1—33；蓝球1个1—16，两个号码区独立 |
| 福彩3D `fc3d` | [目录](https://tb.tuganjue.com/i-l-sd.html) | [目录](https://www.17500.cn/chart/index-1-3d.html) | 百十个3位0—9，保留重复和首位0 |
| 快乐8 `kl8` | [目录](https://tb.tuganjue.com/i-l-kl8.html) | [目录](https://www.17500.cn/chart/index-1-kl8.html) | 20个1—80、不重复、升序展示 |
| 七乐彩 `qlc` | [目录](https://tb.tuganjue.com/i-l-qlc.html) | [目录](https://www.17500.cn/chart/index-1-7lc.html) | 7个基本号及1个特别号，均为1—30，特别号不与基本号重复 |
| 大乐透 `dlt` | [目录](https://tb.tuganjue.com/i-l-dlt.html) | [目录](https://www.17500.cn/chart/index-1-dlt.html) | 前区5个1—35；后区2个1—12，各区内不重复 |
| 排列3 `pl3` | [目录](https://tb.tuganjue.com/i-l-pl3.html) | [目录](https://www.17500.cn/chart/index-1-pl3.html) | 百十个3位0—9，不能套用双色球的去重规则 |
| 排列5 `pl5` | [目录](https://tb.tuganjue.com/i-l-pl5.html) | [目录](https://www.17500.cn/chart/index-1-pl5.html) | 万千百十个5位0—9，保留位置 |
| 七星彩 `qxc` | [目录](https://tb.tuganjue.com/i-l-qxc.html) | [目录](https://www.17500.cn/chart/index-1-7xc.html) | 当前：前六位0—9、末位0—14；20100期之前末位0—9，分版本统计 |

官方规则核对入口：[双色球](https://www.scflcp.com.cn/yxgz/823145252.jhtml)、[福彩3D](https://www.swlc.net.cn/games/3d.html)、[七乐彩](https://www.swlc.net.cn/games/qlc.html)、[大乐透](https://m.lottery.gov.cn/ksjz/m/yxgz_dlt/)、[排列3](https://www.sport.gov.cn/cpzx/n5649/c663326/content.html)、[排列5](https://m.lottery.gov.cn/ksjz/plw/guize/)、[七星彩规则](https://www.nmtc.com.cn/ggtz/21145.html)、[七星彩20100期规则变更公告](https://www.sport.gov.cn/cpzx/n5656/c964843/content.html)。本次不实现奖金计算，因此没有将旧版奖金表套入2026年规则。

## 页面反查证据及限制

已读取上述16个彩种目录，并抽查图感觉的[双色球基本图](https://tb.tuganjue.com/tgj-ssq-kjfb.html)、[福彩3D基本图](https://tb.tuganjue.com/tgj-sd-kjfb.html)、[快乐8基本图](https://tb.tuganjue.com/tgj-kl8-kjfb.html)、[七乐彩基本图](https://tb.tuganjue.com/tgj-qlc-kjfb.html)、[排列3基本图](https://tb.tuganjue.com/tgj-pl3-kjfb.html)、[排列5基本图](https://tb.tuganjue.com/tgj-pl5-kjfb.html)、[七星彩第七位图](https://tb.tuganjue.com/tgj-qxc-dwzs7.html)。大乐透基本图详情请求超时，其规则说明可从目录读取。

可观察到的通用交互包括期数、期号范围、正反序、遗漏开关、逐位分类；部分图还包括缩放、连线、分区和画笔。网页文本中出现模板占位符和旧示例期号，不能当作实时开奖数据。开发环境对两站直接HTTP读取遇到429/503；乐彩网TXT下载入口也未成功取得内容。未把搜索摘要中的号码或网页模板转换为开奖种子数据，未尝试绕过登录、付费或访问限制。

这两站的目录可以作为功能研究范围，但目录存在不等于接口稳定、数据授权或所有指标已核对。

## 本批实现与缺口

| 功能 | 首版状态 | 口径与边界 |
|---|---|---|
| 8种切换、桌面/手机布局 | 已实现 | `/lotteries`；原首页有入口，默认展示已有历史数据的快乐8 |
| 彩种规则与新旧版本 | 已实现 | 输入校验、不同号码区、位置、重复数字、首位0、七星彩规则分界 |
| 最近30/50/100/200/300期 | 已实现 | 取期号范围内最近N条，按开奖先后计算 |
| 期号范围、正反序 | 已实现 | 5位期号转7位；结束期之后的记录不参与统计 |
| 分区号码与逐位分布 | 已实现 | 每个号码区独立；无序彩票位置明确标为“升序第N位”，不是摇出球顺序 |
| 号码频次、出现期数 | 已实现 | 有序数字同一期重复计入出现次数，出现期数仍只加1 |
| 遗漏、遗漏开关 | 已实现 | 按库内记录计数；窗口外更早记录参与；未见过的号码标为“≥”，不保证无缺期 |
| 和值、跨度、奇偶、大小、012路 | 已实现 | 主区/次区/位置分别统计；大小使用全号池口径并显示阈值 |
| 与上条库内记录的重号 | 已实现 | 统计不同号码的集合交集个数，有序位置可单独查看 |
| 单个位置振幅 | 已实现 | 与此前同位置之差的绝对值；没有前条记录时为空 |
| 指标折线及明细表 | 已实现 | SVG，无外部图表CDN依赖；鼠标提示、表格核对 |
| JSON/CSV导入导出与来源 | 已实现 | 按彩种隔离、重复跳过、冲突整批回滚、沿用现有认证 |
| 8彩种自动在线同步 | 部分 | 快乐8沿用原同步；其余7种目前为文件导入，尚无验证可用的在线适配器 |
| 两站特有分组、排序分区、九宫格等 | 未在八彩入口实现 | 既有快乐8实验室保持原样，不自动认为可套用到其他彩种 |
| 全部逐位大小/质合口径对齐 | 未完成 | 两站存在逐位专属大小阈值；某些质合图把1归入“质”。本批不添加未逐项核对的质合图 |
| 画笔、任意缩放、图上连线配置 | 未实现 | 已记录为后续交互范围 |
| 两站完整逐图同输入/同输出验收 | 未完成 | 未将目录读取或相似图形记为1:1通过 |

例如：双色球全池大号17—33、大乐透前区18—35、七星彩当前末位7—14；某些逐位参考页有不同的大小阈值。本批的逐位图明确沿用全号池口径，不冒充与原站的逐位阈值完全一致。

## 数据与接口

新表 `lottery_draws` 的主键为 `(game,issue)`。快乐8继续读写原 `draws` 表，既有 `experiments`、预测特征、模型文件均不修改。新增页面不调用预测或收费第三方实现。

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/lotteries` | 规则、库内记录数、在线同步能力 |
| GET | `/api/lotteries/{game}` | `limit/from/to/version/field`筛选；返回一个活动号码区，避免一次传输全部大型走势图 |
| GET | `/api/lotteries/{game}/export` | 导出该彩种所有记录，包含来源与导入时间 |
| POST | `/api/lotteries/{game}/import` | `draws`或`csv`二选一；可带`source`，最大2MB、10000条 |

`field`为`primary`、`secondary`或`primary:0`等零起始位置；`version`默认为`current`，只有七星彩另支持`legacy`。期号统一为`YYYYNNN`，体彩常见`YYNNN`输入按2000—2099年的两位年份扩展为7位。日期须与期号年份一致且不晚于上海时区的当前日期。规则校验不能证明输入的号码就是官方结果。

CSV表头为`issue,date,primary,secondary`，数组可用空格分隔。JSON为`{"game":"fc3d","draws":[...]}`或记录数组。无第二号码区时`secondary`可省略/空数组。七乐彩、双色球、大乐透、七星彩必须提供第二号码区。七星彩前六位与末位分开填写，避免10—14被误拆为两位数字。

## 验证与运行

```bash
python -m pip install -r requirements.txt
python run.py
# 打开 http://127.0.0.1:8768/lotteries
python -m unittest discover -s tests -v
node --check web/lotteries.js
node tests/check_ui_wiring.cjs
```

真实浏览器脚本：`tests/smoke_lotteries.cjs`。需要环境可解析`playwright`且已安装Chromium，可用`CHROMIUM_PATH`指定可执行文件。它创建临时数据库、加载已有快乐8快照，并只在临时库中为其他7种导入标有“非真实开奖”的测试数据；退出时删除临时库。覆盖切换、文件导入、重复数字、位置、QXC版本、图表、导出回导、来源转义、非法范围及390px手机宽度。

本地验证：89项Python测试通过（本批27项、原有62项），新前端JavaScript语法检查及原界面50个DOM引用检查通过。桌面1440px及手机390px浏览器用例已通过。开发截图使用仓库已有快乐8历史快照，未使用合成开奖结果：

- [桌面截图](previews/eight-lottery-desktop.png)
- [手机截图](previews/eight-lottery-mobile.png)

本批为可部署到现有Python服务的Web首版，不是已上线的国内App。生产环境仍需数据供应、实际开奖对账、多用户权限等后续工作；本批没有执行服务器购买、部署或迁移。
