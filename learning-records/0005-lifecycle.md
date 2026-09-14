# 测试开发全流程：14 天端到端流程地图 + 七大阶段 + 简历话术（收官）

用户已能用一张端到端流程图 + 七大阶段对照表完整讲清"14 天（v3.0 里程碑驱动）每一步输入 / 动作 / 输出 / 工具 / 简历句"，并能口述 M2 是最低可投门禁、POM 五层 vs base_api 四层框架差异、Selenium→Playwright 迁移规则、Locust 鉴权降级方案——这意味着 5 课业务理解系列收官，可合上笔记本按 D1 启动 mall4j。

## 前置基础
- Java + Python 基础语法 / 接口测试基本概念。
- 已学完第 1~4 课：业务全貌、三流合一与状态机、模块边界与可测点、用例设计方法论。

## 本节收获
- 端到端流程图：v3.0 里程碑驱动（D1-D14+，非死线）+ M1 功能+接口 / M2 双自动化+CI（最低可投）/ M3 性能+调优 / M4 mall-ai / M5 投递冲刺（与 M2-M4 并行滚动）。
- 七大阶段速查表：每阶段明确输入 / 动作 / 输出 / 工具 / 简历可写句；遇到"今天该干什么"先查表。
- 双自动化分层：接口框架 = base_api + data/yaml + testcases + reports；UI 框架 = POM 五层 page/base/testcase/common/data。
- Selenium→Playwright 迁移：概念全学（POM / 8 定位 / 显式隐式等待），实现全换（自动等待 + expect 断言，flaky 率更低）。
- 简历 6 句速查：150 用例 / 18 bug + 40 接口 + 80+ 接口自动化 + 12 UI 场景 + GitHub Actions + Locust 3 场景调优复测。
- 数字 ×2 红线：所有数字 ×1 写 = 已等于实际产出，×2 是上限——150 / 80+ / 12 / 18 即上限。
- 风险降级：环境卡住用演示站+Swagger；Locust 鉴权卡住做登录必做+鉴权脚本"待接入"。
- M4 预告：docker-compose + 50 条 Agent 用例 + 4 维度（事实性/工具选择率/拒答率/幻觉率）+ LLM-as-Judge。

## 含义（用户能向面试官讲清楚什么）
- "14 天做什么"：能用一张图讲清 D1-D14+ 七阶段 + M2 即投日常实习。
- "双自动化分层差异"：接口用 base_api 四件套，UI 用 POM 五层；驱动层 Playwright 重写。
- "课程迁移策略"：Selenium 课程按 8.3 迁移 Playwright——概念全学，实现全换。
- "简历数字纪律"：×1 写 = 实际产出 = 上限；面试深问能复现。

**Status**: completed

参见：`../lessons/0005-test-dev-lifecycle.html` · `../reference/0005-lifecycle-cheatsheet.html`
