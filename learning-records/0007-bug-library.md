# 18 条预测缺陷：AGPLv3 模式下的源码逆向工程

用户已能用 5 大源码线索（弱约束 Param / 鉴权链 / 状态机守卫 / 事务边界 / 缓存一致性）独立扫描一个新 Controller 并产出预测缺陷，理解 AGPLv3 协议下"预测缺陷库"模式的设计意图（不直接改源码、基于静态分析的产出物），能讲清 3 条 Critical 缺陷（BUG-002 鉴权 / BUG-011 状态机 / BUG-013 资金事务）的源码引用 + 攻击步骤 + 修复建议三件套——这意味着 M1 阶段"测试设计方法 → 用例库 → 缺陷库"链路打通，下一课可直接进入 Postman 接口调试与完整链路。

## 前置基础
- 已学完第 1-6 课：mall4j 业务定位、三流合一与状态机、模块边界与可测点、测试用例方法论、150 条用例设计、测试开发全流程。
- Java 基础语法（能读懂 Controller / Param / Entity 源码）+ Spring Boot 常用注解（@RestController / @RequestMapping / @Transactional 等）。

## 本节收获
- **AGPLv3 与"预测缺陷库"模式**：mall4j 是 AGPLv3 强 copyleft，对本体源码的修改不能闷声 fork 出去；走"静态分析产出文档"路径既规避协议风险，又能在环境未启动时离线产出硬数字。
- **严重等级 × 优先级矩阵**：Critical=资金/鉴权/数据（3 条），Major=主链路/绕鉴权（6 条），Minor=次要功能（6 条），Trivial=文案/UI（3 条）；优先级 P0=24h / P1=1 周 / P2=1 月 / P3=有空再修。Critical 不一定都 P0，但本课 3 条 Critical 都在主链路所以全是 P0。
- **18 条缺陷三维分布实测**：严重等级 Critical 3 / Major 6 / Minor 6 / Trivial 3；模块 订单支付 5 / 登录注册 4 / 商品 3 / 购物车 3 / 会员权限 3；类型 功能 6 / 安全 3 / 性能 3 / 易用性 2 / 边界 2 / 兼容 2；优先级 P0 6 / P1 6 / P2 4 / P3 2。
- **5 大源码线索**：① 弱约束 Param（@Schema 描述但无 @NotBlank / @Pattern）→ BUG-001；② 鉴权链缺口（无 @SaCheckLogin / SecurityUtils.getUser()）→ BUG-002；③ 状态机守卫缺失（无 @Version 乐观锁）→ BUG-014；④ 事务边界（@Transactional 缺失）→ BUG-013；⑤ 缓存一致性（写 DB 不清缓存）→ BUG-005。
- **TOP 3 Critical 三件套**：BUG-002（鉴权）/ BUG-011（状态机 confirm-submit 缓存替换）/ BUG-013（资金事务 pay/paySuccess 独立调用）每条都有"源码引用 + 攻击步骤 + 修复建议"完整闭环。
- **缺陷生命周期 5 阶段**：发现 → 登记（10 字段模板）→ 复现（步骤可执行化）→ 修复（开发改代码）→ 回归（原用例 + 关联用例全跑绿勾）。
- **数字 ×2 原则**：18 实际产出，简历推荐范围 10-20 个（≥10 不显少、≤20 不浮夸）；最稳写法是 ×1 直接写 18（既顶到上限又不超 ×2 红线 36）；严禁写 36（深问露馅）或 5-9（产出不足）。
- **修复建议常用注解速查**：@NotBlank / @Pattern / @Size / @Min / @Max / @Email / @SaCheckLogin / @PreAuthorize / SecurityUtils.getUser() / @Transactional(rollbackFor=Exception.class) / @Version / @CacheEvict / @TransactionalEventListener(AFTER_COMMIT) / Redisson tryLock。
- **简历金句**：能用"AGPLv3 模式 + 5 大线索 + 18 条预测 + 3 个 Critical"独立讲完一个完整故事，作为"测试工程师硬数字产出"的差异化亮点。

## 含义（用户能向面试官讲清楚什么）
- "为什么用预测缺陷库而不是真实复现"：AGPLv3 边界（不能闷声改源码）+ 环境未启动时静态分析也能产出 + 设计阶段 18 条硬数字落地。
- "5 大源码线索怎么扫出来 BUG-002"：打开 UserRegisterController 第 78-100 行 updatePwd()，方法签名无 @SaCheckLogin / @PreAuthorize，方法体首行未调用 SecurityUtils.getUser()，MallWebSecurityConfigurerAdapter 又 permitAll——线索 ② 命中。
- "Critical 缺陷的修复主线"：BUG-002 = 加注解 + 白名单收窄 + 审计日志；BUG-011 = 缓存 key 扰动 + token 校验 + TTL；BUG-013 = 加 @Transactional + 合并 Service 方法 + 幂等锁。
- "数字 18 怎么写简历"：直接写"发现 18 个有效 Bug（含 3 个 Critical 鉴权/状态机/资金类）"，×1 顶到上限不超 ×2 红线 36。
- "AGPLv3 边界如何坚守"：本课产出物是"基于源码的缺陷文档"而非代码修改，可独立放进二开仓库（如 mall4j-test-practice），不构成"分发修改"。
- "18 条分布的特征指纹"：Critical 集中在鉴权 + 资金（登录注册 1 + 订单支付 2）；订单支付 5 条最多反映状态机复杂；安全 3 条对应鉴权/水平越权/资源越权 3 类典型攻击。

**Status**: active

参见：`../lessons/0007-bug-library-18-predicted.html` · `../reference/0007-bug-library-cheatsheet.html` · `../test-cases/M1-D3-001/bug-list.csv` · `../test-cases/M1-D3-001/bug-list.md`
