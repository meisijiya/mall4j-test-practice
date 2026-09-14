# 模块边界 + 横切关注点必测点：七模块包归属 + 五横切 4/3/3/4/6 必测

用户已能用第 2 节"七大模块边界对照表"按业务模块划分 pytest 用例（test_api_user.py / test_api_admin.py / test_ui.py / test_perf.py 至少 4 文件），并用第 3-7 节鉴权 4 + 幂等 3 + 分布式锁 3 + 参数校验 4 + 分页 6 必测矩阵，对任意 mall4j 接口快速识别 ≥3 个可测点；这意味着 M1 阶段"测什么"已讲清，下一课可进入"怎么测"——pytest + Knife4j 把测点变成接口自动化用例。

## 本节收获
- 接口契约唯一可信源 = `yami-shop-api` 的 Knife4j（`localhost:8086/doc.html`），管理端文档常滞后。
- 鉴权 4 必测：A1 不带 token → 401、A2 过期 token → 401、A3 普通用户越权 admin → 403（OWASP Top 10）、A4 多角色菜单并集；只测 A1 是反模式。
- 幂等 3 必测：I1 重复 orderNumber、I2 重复 payNo（乐观锁 `version+1`）、I3 重复 refundNo（唯一索引）；只测"正常下单一次成功"是反模式。
- 分布式锁（Redisson `@RedisLock`）3 必测：L1 100 并发扣库存（预置 50）不超卖、L2 50 并发同订单号仅 1 成功、L3 锁过期边界 4.9s 不早释；面试金句 = "超时时间 + 业务时长必须配对，业务 > 5s 必须显式指定 `expire`"。
- 参数校验 4 必测（Jakarta Validation `@Valid`）：V1 必填缺失、V2 类型错误、V3 长度超限、V4 枚举非法；粒度 = 字段级，错误信息 `msg` 必须指出"哪个字段错了"。
- 分页 6 必测（MyBatis-Plus `PageParam`，`size` 最大 100）：P1 `current=0` / P2 `current=-1` / P3 `size=0` / P4 `size=99999` / P5 total=0 / P6 total=1；订单明细分页手写 SQL 需验 `total` = 订单数而非订单项数。
- 反模式警告：孤立测"点"不写进用例库；判断标准 = 这条用例单独跑通 ≠ 业务能跑通，必须把"点"串成"流"。

## 含义（用户能向面试官讲清楚什么）
- "七个模块怎么归属后端包"：能说 7 行包路径表 + 测试归属列 + 主测试方法列。
- "鉴权怎么测才够"：A1+A3 是接口自动化的最低要求，A2/A4 是线上最常爆雷的点。
- "Redis 分布式锁不是银弹"：超时与业务执行时长配对，超时先于业务完成 = 锁失效 = 并发问题。
- "为什么 A3 垂直越权比 A1 不带 token 更值得测"：A1 几乎所有系统都做了，A3 才是真正区分测开能力的点。
- "字段粒度 vs 一条'参数错误'用例"：覆盖率差距 = 字段数 × 边界点数；前者按字段展开，后者只走通 1 条异常路径。

**Status**: active

参见：`../lessons/0003-module-boundary-test-points.html` · `../reference/0003-test-points-cheatsheet.html`