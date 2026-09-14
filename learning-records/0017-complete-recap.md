# learning-record 0017 · mall4j 完整收尾 + 简历包

> **记录时间**：2026-09-14
> **触发条件**：M5-D14-001 done 后自动触发（feature-driven-lessons skill）
> **关联**：resume.md + docs/3-github-repos/ (mall4j-test-practice + mall4j-auto-test + agent-eval-practice README) + init-repo.sh

## 10 条 bullets（5 段：简历包装 / 3 仓库 / 投递闭环 / 教学沉淀 / 教训）

### 简历包装
1. **数字 ×2 原则是简历红线**：所有可写数字 = 实际产出 × 2 不超；本次校验 10 项（150/80+/12/18/24/120/50/4/4/4）全部不超，深问才稳
2. **动词控制表是测开岗简历灵魂**："参与、协助、独立负责XX模块" 替代 "主导、负责、统筹"；"覆盖核心场景" 替代 "覆盖率 95%"
3. **技术栈分级是真假防火墙**：✅ 可写（Python/pytest/Playwright/POM/YAML/Allure） / ⚠️ 慎写（Jenkins MCP/RAG 原理/性能调优细节） / ❌ 别写（LangGraph 源码/LLM 训练/自研框架）

### 3 仓库设计
4. **3 仓库拆分遵循能力维度分离**：test-practice（测试设计）/ auto-test（自动化）/ agent-eval（AI 测试）三段互不重叠
5. **README 8 段标准结构**：仓库一句话 + 仓库内容 + 简历可写句子 + 数字校验表 + 核心交付物清单 + 5 类深问答案 + 使用命令 + 关联仓库 / 协议 / 联系方式
6. **init-repo.sh 三模式**：bash test-practice / auto-test / agent-eval，从主仓选择性复制对应产物，避开"全量塞进单仓"的 README 过长 + 协议混淆

### 投递闭环
7. **M2 即最低可投状态**：本次 13/13 完成时反而更应立即投递（深度建设与投递并行两不耽误）；M2 达成后滚动投递实习僧/BOSS 日常实习每周 15-20 家
8. **5 类高频追问答案框架**：选 mall4j（业务贴近 + 体量 + 避免造轮子） / 18 缺陷（静态分析 + 业务反推 + 场景组合） / 性能瓶颈（TPS + P99 + 错误率 + 调优决策树） / 接口框架（5 层） / Agent（4 维度 + 4 类 + LLM-as-Judge）

### 教学沉淀
9. **lesson 0017 = 13/13 收官课**：5 段结构（13 features 完成表 + 5 阶段汇总 + 简历包装规则 + 3 仓库设计 + 投递闭环）+ 8 张表 + 1 个 mermaid 流程图 + 3 题 quiz 自检
10. **M4 mall-ai 是独立项目独立 harness**：AGPLv3 边界严格遵守，PROJECT_TARGET_BOOK §2.2 已明示；M4 D12-D13 由 mall-ai-after-sales-platform 仓承接，本仓 feature_list 不登记

## 9 段含义（每段 1 句"为什么这样做"）

1. **数字 ×2 原则**：实际产出 150 条就写 150（不超）；如果想写 300 必须实际产出 ≥ 150；原因是面试官会追问"具体哪 150 条"，超了就露馅
2. **动词控制**：实习岗定位用"参与、协助"是简历常态，"主导、统筹"是领导岗；面试官看到后者会问"你带几个人"答不上来
3. **技术栈分级**：每个技能都分可写 / 慎写 / 别写三类，目的是把"主攻栈做深" / "了解栈讲清异同" / "完全不懂的不碰" 三档分明
4. **3 仓库能力维度分离**：测试设计 / 自动化 / AI 测试 是测开岗 3 个核心能力维度；放一起面试官扫读效率低；分开后每个仓库都聚焦一种能力
5. **README 8 段标准结构**：面试官平均 3 分钟扫一个仓库，结构化能让 ta 快速定位关键信息（数字 + 简历句子 + 使用命令）
6. **init-repo.sh 三模式**：避免每个仓库都要手动 `cp -r` 一遍；统一脚本降低用户操作成本；`bash -n` 校验防止脚本语法错
7. **M2 立即投递**：不等"完美"是因为投递反馈能反向指导补强；继续闭门造车可能做错方向（如花时间做性能但目标公司只问接口）
8. **5 类高频追问**：boss 直聘 / 拉勾 / 实习僧的测开岗 JD 高频词云排序后的前 5 类；答案框架给的是"骨架"，具体细节根据项目展开
9. **M4 mall-ai 独立 harness**：AGPLv3 边界 + Apache-2.0 协议不同 + 测试方向不同（功能 vs AI）；硬塞进 mall4j 会破坏 PROJECT_TARGET_BOOK §2 双项目联动设计

## 4 件本 feature 独有 fix（M5-D14-001 专属，非通用）

### fix 1：README 8 段结构是面试官扫读优化，不是随意列

**问题**：第一版 README 只写了"仓库内容 + 使用命令" 4 段；面试官反馈"看不出这仓库能证明什么能力"

**修法**：补全 8 段（仓库一句话 + 简历可写 + 数字校验表 + 核心交付物 + 5 类深问答案 + 关联仓库 + 协议 + 联系方式）；简历可写句子直接复用 resume.md 的 STAR 句

**位置**：`docs/3-github-repos/*/README.md`（三仓统一结构）

### fix 2：init-repo.sh 必须支持三模式分支，不能 3 个脚本

**问题**：第一版写了 3 个独立脚本（init-test-practice.sh + init-auto-test.sh + init-agent-eval.sh），用户得记住 3 个脚本名 + 3 个用法

**修法**：合并成 `init-repo.sh <type>` 三模式分支；type 只能是 `test-practice | auto-test | agent-eval`；其它报 `[ERROR]` 退出

**位置**：`docs/3-github-repos/init-repo.sh`（254 行 case 分支）

### fix 3：AGPLv3 vs Apache-2.0 双协议仓库必须分开

**问题**：第一版想用 1 个 `mall4j-mall-ai-all-in-one` 大仓；结果 LICENSE 文件冲突（AGPL-3.0 强 copyleft 污染了 mall-ai 的 Apache-2.0 代码）

**修法**：拆 3 仓库（mall4j-test-practice + mall4j-auto-test 用 AGPL-3.0；agent-eval-practice 用 Apache-2.0）；每个 README 末尾明确"协议继承自上游项目"

**位置**：`docs/3-github-repos/*/README.md` §"协议"段

### fix 4：数字 ×2 校验必须做成表格，不能口头说"我控制了"

**问题**：第一版简历 v2 用"覆盖大量接口"模糊表述；面试官追问"具体多少" 答"七八十吧" → 印象分掉

**修法**：resume.md §"简历数字校验" + 每个 README 都加一张"实际 vs 简历 vs ×2 校验"表；表格让面试官自己看到"150 条 = 实际 150 条"

**位置**：`resume.md` §"简历数字校验" + `docs/3-github-repos/*/README.md` §"简历数字校验"

## 引用路径段（4 个）

- **resume.md**：`<mall4j>/resume.md` —— 简历 v3 主体（6.2KB / 6 段结构）
- **mall4j-test-practice README**：`<mall4j>/docs/3-github-repos/mall4j-test-practice/README.md` —— 测试设计仓库
- **mall4j-auto-test README**：`<mall4j>/docs/3-github-repos/mall4j-auto-test/README.md` —— 自动化仓库
- **agent-eval-practice README**：`<mall4j>/docs/3-github-repos/agent-eval-practice/README.md` —— AI 测试仓库
- **init-repo.sh**：`<mall4j>/docs/3-github-repos/init-repo.sh` —— 三模式初始化脚本
- **PROJECT_TARGET_BOOK.md**：`<workspace>/D:/26测试/PROJECT_TARGET_BOOK.md` —— §5 简历包装规则 + §6 面试守则 + §10 决策记录
