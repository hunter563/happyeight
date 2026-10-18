# 第三方代码与许可

本仓库为四个第三方项目的个人非商业研究集成。上游代码仍归原作者所有，各目录中的许可证和声明独立适用；本仓库不将上游代码重新许可。

| 目录 | 作者/来源 | 上游许可情况 |
|---|---|---|
| vendor/kl8-analyzer | KittenCN/kl8-lottery-analyzer | MIT，保留 LICENSE |
| vendor/lottery-lab | gin-18/lottery | MIT，保留 LICENSE |
| vendor/luck8 | fightingfor/Luck8 | README 声明 MIT；当前快照没有独立 LICENSE 文件，未补造授权文本 |
| vendor/luckydd | FanKang2021/LuckyDD | README 明确“仅供学习研究使用，不得用于商业目的” |

新增集成代码同样仅用于本仓库个人非商业研究，不授予第三方作品额外权利。商业使用须分别核对各上游的当前许可并取得需要的授权。

上游原文件保留。仅移除了 Luck8 抓取器中的硬编码会话Cookie。分发不包含 `.git` 历史、安装依赖 `node_modules`、`__pycache__` 和编译生成的 `dist`。

LuckyDD TypeScript 纯函数在运行时使用 Node.js 官方类型剥离功能载入。适配器截取数据库包装器之前的导出函数并移除数据库导入，不修改原统计文件。原遗漏函数的两个边界问题在适配层修正。

原版算法的随机评分、过时奖金表和有目标泄露的期望值函数不参与融合输出。源码仍用于审阅与研究，不表示它们经过认证或适合直接使用。
