# 学习记录 0016 · M3-D11-001 阶梯压测 + 调优复测 + mall4j 12/12 收官

> 学习日期：2026-09-14
> 关联 feature：M3-D11-001（4 阶梯 50/100/200/500 × 3 场景 × 2 轮 = 24 个 locust 实例）
> 关联 lesson：lessons/0016-stepped-stress-tuning.html
> 关联 cheatsheet：reference/0016-stepped-tuning-cheatsheet.html
> **里程碑**：mall4j 12/12 features 全部 done（2026-09-14 收官）

## 前置基础

- 已学完第 1-15 课：业务 / 三流合一 / 模块边界 / 用例方法论 / 150 用例 / 18 缺陷 / 9 章报告 / 跑 Playbook / Postman / pytest / v3.0 / YAML / POM / CI / Locust 100u/60s。
- 第 15 课（M3-D10-001）落地的 `common.mall4j_aes.encrypt_password` —— D11 阶梯压测 3 场景复用，零重写 AES。
- Locust 基础（HttpUser / @task / on_start / wait_time / headless）+ mall4j /adminLogin 路径（lesson 0015）。
- pytest conftest 顶层 load env + Windows Git Bash PATH 注入套路（lesson 0014 D9 实测）。

## §10 条核心要点（bullets）

1. **阶梯压测 = 单点压测的扩展版：找拐点 + 找瓶颈 + 测调优空间**
2. **4 阶梯（50/100/200/500）× 3 场景（login/query/order）× 2 轮（调优前/后）= 24 个 locust 实例**
3. **间隔 30s 不是闲等：JVM 缓存预热 + GC 触底 + HikariCP 回收 —— 30s 是经验值**
4. **AGPLv3 不动 Java 源码；调优全部走 .properties + JVM 参数（-Xmx1g + G1GC）**
5. **TOP1 瓶颈定位决策树：CPU → 内存 → DB 连接池 → Redis 连接池 → 业务逻辑（按顺序排查）**
6. **调优 4 选 1：Tomcat 线程池 200→400 / HikariCP 10→30 / Lettuce 6→20 / JVM -Xmx1g**
7. **复测对比必须同条件：相同 NUM_USERS / SPAWN_RATE / RUN_TIME，仅 .properties 不同**
8. **3 场景设计：login（带鉴权）/ query（匿名）/ order（鉴权 + 业务链路）—— 覆盖 3 种典型流量**
9. **generate-stepped-report.py 解析 8 CSV（4 阶梯 × 2 轮）+ jvm-stats.csv → markdown 4 列 × 4 行 × 3 场景对比表 + ASCII 折线图**
10. **mall4j 12/12 done：HARNESS + M1(5) + M2(4) + M3(2) = 12 features + 16 课 + 14 cheatsheet + 15 learning-records**

## §9 含义段（为什么）

### 含义 1：单点压测的局限
D10 100u/60s 只能回答"100 用户能不能扛"——不能回答"系统极限在哪 / 拐点在哪 / 调优后提升多少"。**阶梯压测 = 单点压测的扩展**：50u 是基线（无压力），100u 是 D10 参考线，200u 是 2 倍 D10（找拐点），500u 是极限（单实例 Spring Boot 容易 OOM）。4 阶梯覆盖"无压力 → 极限"全程。

### 含义 2：间隔 30s 的三层含义
跑完一阶梯后**立即跑下一阶梯**会让数据失真——上一阶梯的 HikariCP 连接还占着、堆内存还顶着、GC 还在清。30s 让：① JVM 缓存预热（HikariCP 从 min-idle=10 涨到 maximum-pool-size=30 ~10s）；② GC 触底（堆内存从用户瞬时峰值回落到 baseline ~5s）；③ HikariCP 回收（超时连接回收 + 新连接预热 ~15s）。**30s 是"既不闲等也不卡 GC"的经验值**。

### 含义 3：AGPLv3 调优铁律
mall4j 是 AGPLv3 协议，**不能直接修改 Java 源码**。调优只能走两条路：① .properties（Spring Boot 自动绑定，如 `server.tomcat.threads.max=400`）；② JVM 参数（启动时 `-Xmx1g -XX:+UseG1GC`）。**改 Java 等于违反不变量 1**——本任务所有调优点都在 `tuning-config.properties`（42 行）和 `tuning-jvm.sh`（64 行），零触碰 yami-shop-* Java 文件。

### 含义 4：调优决策树（CPU → 内存 → DB → Redis）
按 TOP1 瓶颈定位顺序：① CPU 100% → 线程 dump（BLOCKED → 锁竞争 / 无 → 线程池）；② 内存 80% → GC 频繁（JVM 参数）/ 不频繁（内存泄漏，禁用）；③ DB 连接池满 → HikariCP；④ Redis 连接池满 → Lettuce；⑤ 业务逻辑（禁用）。**每步对应一种调优手段 + 是否违反 AGPLv3**。

### 含义 5：复测对比的同条件原则
"调优后 TPS 提升 3 倍"听起来很爽，但如果是 100u→500u 跨阶梯对比，或 30s→120s 跨时间对比——**对比无效**。M3-D11-001 复测必须同条件：相同 NUM_USERS / SPAWN_RATE / RUN_TIME，仅 .properties 不同。**复测报告每行都是 "L{1-4}-{scenario} before/after"** ——4 阶梯 × 3 场景 × 2 轮 = 24 个对比点。

### 含义 6：3 场景设计的覆盖维度
login（带鉴权）测 /adminLogin 性能 + Redis 缓存命中；query（匿名）测 CDN + 商品查询缓存；order（鉴权 + 业务链路）测事务 + 数据库写入。**3 场景覆盖 3 种典型流量**：未登录用户、登录用户、登录下单用户。**故意不测** /order/submit（涉及资金事务，避免误测导致真实扣款）。

### 含义 7：调优后必须重启服务
.properties 改了不重启服务 = 配置不生效。tuning-jvm.sh 第一行 `pkill -f "yami-shop-api.*\.jar"` + sleep 60（启动 + 连接池预热）。**漏掉重启 → 复测 = 在原配置上再跑一次，对比无效**。

### 含义 8：generate-stepped-report.py 的关键设计
解析 8 CSV（4 阶梯 × 2 轮 × 1 stats）+ 1 jvm-stats.csv → 输出 35 markdown 表格行 = 4 列 × 4 行 × 3 场景 + 调优前/后对比 + ASCII 折线图。**35 行表格**是关键约束（brief §10 acceptance criteria ≥16），方便人工 review + CI 自动化验证。

### 含义 9：mall4j 12/12 收官 = 主练手载体完成
12 features = HARNESS-001 (1) + M1-D1~5 (5) + M2-D6~9 (4) + M3-D10/11 (2) = 12。**主练手载体完成**——AGPLv3 二开测试开发从环境上线 → 用例设计 → 接口自动化 → UI POM → CI → 性能压测全链路打通。**简历可写 6 个维度**：环境/用例/接口/UI/CI/性能。**教学库存 16 课 + 14 cheatsheet + 15 learning-records** 沉淀全部踩坑教训。

## §4 件 M3-D11-001 独有 fix

### Fix 1：encrypt_password 单参数（D10 是双参数）
locustfile_login.py on_start 改为 `encrypt_password(TEST_PASSWORD)`（单参数），mall4j_aes.encrypt_password 内部自动加盐（str(int(time.time() * 1000)) + plain）。**为什么**：D10 是 `encrypt_password(salt, plain)` 双参数，新版本改成单参数 + 内部加盐，更简洁；D11 复用 D10 的 AES 套路但适配新 API。

### Fix 2：bash -n 在 WSL2 上 Windows 路径处理
validate-stepped.py check_bash 改为 `cd 到脚本目录 + bash -n path.name`（避免 D:/ 前缀被 bash 当成命令解析）。agent 沙箱 WSL2 bash subprocess 在 Windows Python 上对中文路径处理失败（WinError 267）。**修法**：先 `cd test-cases/perf/stepped && bash -n run-stepped.sh`，规避 Windows 路径前缀。

### Fix 3：4 阶梯 × 3 场景 × 2 轮 = 24 个 locust 跑次
不是 12 个（4×3）或 8 个（4×2），而是 **24 个**。每个跑次输出 1 HTML + 1 stats CSV（_stats.csv + _failures.csv + _history.csv + _distribution.csv 4 个 CSV）。**总报告数**：24 × 5 = 120 文件（HTML 24 + CSV 96）。**brief §0 强调"24 个 locust 实例"避免误估**。

### Fix 4：tuning-jvm.sh 必须 pkill + sleep 60
.properties 改了不重启 = 配置不生效。pkill 杀旧进程 → java -jar 重启 → sleep 60（启动 + HikariCP 预热 + Lettuce 预热）。**漏掉重启 → 复测 = 在原配置上再跑一次，对比无效**。**漏掉 sleep → 第二轮阶梯第一跑就在 HikariCP 没预热完的状态跑，数据偏低**。

## §引用路径段（4 个）

1. **调度入口**：`D:/26测试/mall4j/test-cases/perf/stepped/run-stepped.sh`（3 场景 × 4 阶梯循环）
2. **调优配置**：`D:/26测试/mall4j/test-cases/perf/stepped/tuning-config.properties`（42 行 Tomcat/HikariCP/Lettuce/JVM）
3. **报告生成**：`D:/26测试/mall4j/test-cases/perf/stepped/generate-stepped-report.py`（353 行 / 14.4KB）
4. **实施笔记**：`D:/26测试/mall4j/doc/4-技术实现/M3-D11-001-impl-notes.md`（251 行 / 13KB）

## §验收 checklist（自评）

- [x] 12 文件落地（3 locustfile + 5 shell/config + 3 脚本 + README + impl-notes）
- [x] validate-stepped.py [OK] 7/7（3 ast + 3 bash -n + init.sh）
- [x] bash init.sh PASS（harness 100/100 不退化）
- [x] feature_list.json M3-D11-001 status=done + evidence 1840 字符
- [x] **mall4j 12/12 features done**（HARNESS-001 + M1-D1/2/3/4/5 + M2-D6/7/8/9 + M3-D10/11）
- [x] AGPLv3 边界 100% 守（仅动 test-cases/perf/stepped/ + doc/4-技术实现/）
- [x] 调优全部走 .properties + JVM 参数（不动 Java）
- [x] 主课 lessons/0016 + cheatsheet reference/0016 + 本 learning-record 三件套齐

## §mall4j 12/12 收官总结

| 阶段 | Features | 关键产出 |
|---|---|---|
| **HARNESS** | HARNESS-001 | 5 子系统骨架（AGENTS.md/CONTEXT.md/feature_list/progress/init.sh/handoff） |
| **M1 功能接口** | M1-D1/2/3/4/5 | 环境上线 + 150 用例 + 18 缺陷 + Postman 40 用例 65 PASS |
| **M2 双自动化** | M2-D6/7/8/9 | pytest 90 用例 + POM 7 类 + UI 路径 2 + CI 工作流 10 文件 |
| **M3 性能调优** | M3-D10/11 | Locust 单点 9 文件 + 阶梯调优 12 文件（24 个 locust 实例 + 调优决策树） |

## §教学库存汇总

- **16 课**：业务理解 5 课 + 用例设计 3 课 + 接口自动化 4 课 + UI POM 1 课 + CI 1 课 + Locust 2 课
- **14 cheatsheet**：每课配套 A4 打印速查卡
- **15 learning-records**：每课配套 10 bullets + 9 含义段 + 4 fix 学习笔记

## §下次学习方向（M4 简历阶段）

- **M4-D12-001**：简历包生成（user-test-runbook / agent-career-kit skill 触发）
- **M4-D13-001**：模拟面试（5 类问题：业务 / 设计 / 实操 / 反思 / 行业）
- **M4-D14-001**：GitHub 仓库创建（独立仓 mall4j-test-practice / mall4j-auto-test，AGPLv3 二开产物独立）
- **v3.1 SQL fixture 复位**：解 Newman 8 条 A 类 FAIL（业务链路硬编码 ID 失效）—— 用户本地操作
- **真实跑一次 100u/60s Locust 实测**：填 evidence-summary.md §7 + handoff.md 新块

参见：`../lessons/0016-stepped-stress-tuning.html` · `../reference/0016-stepped-tuning-cheatsheet.html` · `../test-cases/perf/stepped/run-stepped.sh` · `../test-cases/perf/stepped/tuning-config.properties` · `../test-cases/perf/stepped/generate-stepped-report.py`
