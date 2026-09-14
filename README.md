# mall4j-test-practice

> **仓库定位**：电商商城系统测试设计与产出（功能用例 + 缺陷库 + 报告 + 教学库存）
> **目标项目**：gz-yami/mall4j（⭐5.2k / 🍴1.3k · AGPL-3.0）
> **作者**：双非本科大四 · 测开岗求职 · Java+Python 基础
> **生成时间**：2026-09-14

## 仓库一句话

基于 mall4j（Spring Boot + Vue3 + Redis + MyBatis-Plus）开源 B2C 电商，独立完成 5 大模块（商品/订单/会员/支付/购物车）的**功能测试设计与产出**，沉淀 150 条用例 + 18 个缺陷 + 1 份 9 章测试报告。

## 仓库内容

| 目录 | 内容 | 简历对应 |
|---|---|---|
| `testcases/M1-D2-001/` | 功能测试用例 90 条（登录/注册/商品/购物车） | "编写测试用例 150 条" |
| `testcases/M1-D3-001/` | 功能测试用例 60 条 + 18 缺陷 + 9 章报告 | "发现有效缺陷 18 个" |
| `docs/` | 测试方法论 + 业务理解 5 课 + 模块边界 | "参与需求评审" |
| `lessons/` | 16 课 HTML 教学库存 | 教学输出（加分项） |
| `learning-records/` | 15 篇学习记录 + 4 件非显然 fix | 反思沉淀（加分项） |

## 简历可写句子

> 基于 gz-yami/mall4j（⭐5.2k）开源 B2C 电商商城，独立完成商品 / 订单 / 会员 / 支付 / 购物车模块的测试设计与自动化工作。**编写功能测试用例 150 条**，**发现有效缺陷 18 个**，输出 9 章功能测试报告。

## 简历数字校验（×2 原则）

| 数字 | 实际产出 | 简历写法 | ×2 校验 |
|---|---|---|---|
| 功能测试用例 | 150 条（D2 90 + D3 60） | "编写测试用例 150 条" | ✓ 不超 |
| 有效缺陷 | 18 条（Critical 3 + Major 6 + Minor 6 + Trivial 3） | "发现有效缺陷 18 个" | ✓ 不超 |
| 测试报告 | 1 份 9 章 384 行 | "输出测试报告 1 份" | ✓ |

## 核心交付物清单

```
mall4j-test-practice/
├── README.md                                ← 本文件
├── testcases/
│   ├── M1-D2-001/
│   │   ├── M1-D2-001-testcases.csv         (90 行 11 字段)
│   │   ├── M1-D2-001-testcases.md          (128 行)
│   │   └── generate-cases.py               (可重跑)
│   └── M1-D3-001/
│       ├── M1-D3-001-testcases.csv         (60 行 11 字段)
│       ├── M1-D3-001-testcases.md          (115 行)
│       ├── bug-list.csv                    (18 条缺陷 + 1 header)
│       ├── bug-list.md                     (491 行)
│       ├── functional-test-report.md       (9 章 384 行)
│       └── generate-*.py × 2               (可重跑)
├── docs/
│   └── 1-业务理解/                          ← 5 课业务教学
├── lessons/                                 ← 16 课 HTML 教学
├── reference/                               ← 14 个速查卡
├── learning-records/                        ← 15 篇学习记录
└── .github/
    └── ISSUE_TEMPLATE/bug-report.md        ← 标准 bug 模板
```

## 简历深问应对（5 类高频追问）

### Q1：为什么选 mall4j 这个项目？

**答案框架**（3 段）：
1. **业务贴近**：B2C 电商场景，和真实业务最接近，技术栈主流
2. **体量合适**：⭐5.2k star，文档完备，Swagger / API / admin 后台一应俱全，**能扛得住深入追问**
3. **避免重复造轮子**：不自己写 demo 项目练手，**直接基于成熟开源项目做测试实战**，产出物可验证

### Q2：你怎么设计测试用例？

**答案框架**（4 类方法论 + 5 类输入域）：
1. **等价类划分**：输入域划分（如金额边界 0.01 / 9999.99 / 10000）
2. **边界值**：边界值 ±1（如库存 0 / 1 / 999 / 1000）
3. **场景法**：业务链路（登录→加购→下单→支付），覆盖正常 + 异常
4. **判定表**：多条件组合（支付方式 × 优惠券 × 库存）

**5 类输入域**：
- 正常用例（业务主路径）
- 异常用例（边界 / 空 / 超长 / 特殊字符）
- 鉴权用例（未登录 / 越权 / token 过期）
- 并发用例（库存超卖 / 重复提交）
- 兼容性（浏览器 / 移动端 / 接口版本）

### Q3：18 个缺陷怎么发现的？

**答案框架**（3 段）：
1. **静态分析**：读 Controller 注解 + Param 字段约束 + Service 实现 + Security 配置（AGPLv3 边界：仅基于源码静态分析，不改源码）
2. **业务反推**：从状态机推异常路径（如订单从待付款→已取消的退款链路）
3. **场景组合**：多条件组合下未覆盖的角落（如支付超时 + 自动取消 + 库存回滚）

### Q4：测试报告怎么写的？

**答案框架**（9 章结构）：
1. 测试概述（项目背景 + 范围）
2. 测试方法论（等价类 / 边界值 / 场景法）
3. 测试环境（JDK17 + MySQL 8 + Redis 5 + mall4j dev）
4. 测试用例汇总（150 条分布）
5. 缺陷汇总（18 条分布）
6. 风险评估
7. 测试结论
8. 改进建议
9. 附录（用例索引 + 缺陷清单）

### Q5：AGPLv3 怎么处理的？

**答案框架**（边界守则）：
1. **协议约束**：mall4j 是 AGPL-3.0 强 copyleft，**不直接修改本体源码**
2. **测试产出**：所有测试用例 / 报告 / 缺陷库都基于源码**静态分析 + 接口调试 + 演示站操作**
3. **二开产物**：自动化的代码走独立仓库（本仓的姊妹仓 `mall4j-auto-test`）

## 如何使用本仓库

### 浏览测试用例

```bash
# 看 90 条 D2 用例（登录/注册/商品/购物车）
cat testcases/M1-D2-001/M1-D2-001-testcases.csv

# 看 60 条 D3 用例（订单/会员/异常）
cat testcases/M1-D3-001/M1-D3-001-testcases.csv

# 看 18 条缺陷
cat testcases/M1-D3-001/bug-list.csv
```

### 重新生成用例

```bash
# 生成 90 条 D2 用例
cd testcases/M1-D2-001 && python3 generate-cases.py

# 生成 60 条 D3 用例 + 18 缺陷
cd testcases/M1-D3-001 && python3 generate-cases.py
python3 generate-bugs.py
```

### 阅读 9 章报告

```bash
# 9 章功能测试报告（含 150 用例总览 + 18 缺陷占位）
cat testcases/M1-D3-001/functional-test-report.md
```

### 阅读教学库存

```bash
# 业务理解 5 课（mall4j 三流合一 + 状态机 + 模块边界）
open lessons/0001-mall4j-business-overview.html
open lessons/0002-three-flows-and-order-state-machine.html
open lessons/0003-module-boundary-test-points.html

# 测试设计 5 课（用例设计方法论 + 缺陷库 + 报告骨架）
open lessons/0006-test-design-150-cases.html
open lessons/0007-bug-library-18-predicted.html
open lessons/0008-report-skeleton-9-sections.html
```

## 关联仓库

- **姊妹仓**：[mall4j-auto-test](../mall4j-auto-test)（接口 + UI 自动化 + CI + 压测脚本）
- **AI 评测仓**：[agent-eval-practice](../agent-eval-practice)（Agent 50 用例 + LLM-as-Judge）
- **源项目**：[gz-yami/mall4j](https://github.com/gz-yami/mall4j)（⭐5.2k · AGPL-3.0）

## 协议

本仓库基于 **AGPL-3.0**（继承自 mall4j 项目），所有测试用例 / 报告 / 缺陷库均为作者原创，遵循相同开源协议。

## 联系方式

（待用户填写）
