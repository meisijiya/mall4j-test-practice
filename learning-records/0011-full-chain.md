# Postman v3.0 完整链路 40 条用例：探针机制 + 5 业务码 + 6 folder 链路依赖

用户已能从 v2.1 的 20 条骨架跃升到 v3.0 的 40 条完整链路用例，能讲清"探针机制 + 5 业务码 + 双写策略 + 6 folder 链路依赖"4 个核心：理解为何探针请求自动从 `/prod/prodInfo` 拿真实 prodId/skuId 而不是 SQL 预填、为什么业务码断言必须用 `String(j.code)` 而不是 200、为什么 Newman `{{token}}` 解析优先 environment 导致必须双写、为什么拆 6 folder 把支付独立——这意味着 M1-D5-001（Postman v3.0）落地，下一步进入 M2-D7-001（pytest + UI 自动化框架）。

## 前置基础
- 已学完第 1-10 课：mall4j 业务定位 / 三流合一与状态机 / 模块边界与可测点 / 用例方法论 / 150 条用例设计 / 18 条预测缺陷 / 9 章报告骨架 / Postman API 测试 / pytest requests 测试。
- 第 9 课（Postman）+ 第 10 课（pytest）的实跑验证 — D5 v3.0 是第 9 课的"完整链路升级"。
- Java 源码阅读能力（ShopCartController / MyOrderController / PasswordManager）。
- Newman CLI + Node.js 全局包（crypto-js）+ Python 3.x + JSON 序列化基础。

## 本节收获
- **探针机制（L3.1 + L3.2 两次 GET）**：D4 v2.1 失败根因是 env 写死 `prodId=18/skuId=10` 但跨商品（18 是手机壳、10 是数据线），加购永远 404。v3.0 在 Folder 3 头部加 2 条探针 item（`GET /prod/prodInfo?prodId=1` + `GET /sku/getSkuList?prodId={{prodId}}`），Tests 脚本 `pm.collectionVariables.set('skuId', _v[0].skuId) + pm.environment.set('skuId', _v[0].skuId)` 双写回 env，下游 L3.3/L4.1/L4.2 用 `{{skuId}}` 引用真实值。
- **5 业务码断言模板（不是 2 套）**：T-A `'00000'` 成功 26 条 / T-B `'A00001'` 业务异常 3 条 / T-D `'A00014'` @NotBlank 校验 2 条 / T-E `'A00005'` 服务端异常 1 条 / T-F `!='00000'` 宽松 8 条（含鉴权无业务码）。D4 只覆盖 T-A + T-B，v3.0 把校验失败 / 服务异常 / 鉴权场景都纳入。
- **业务码是 String 不是 Integer**：mall4j 后端 `ServerResponseEntity.code` 是 `String` 类型，JSON 序列化 `code="00000"`。Postman 默认断言 `pm.expect(j.code).to.eql(200)` 永远 FAIL（200 是数字、code 是字符串）；正确写法 `pm.expect(String(j.code)).to.eql('00000')` — 显式转字符串。
- **Newman `{{}}` 解析作用域**：header 引用 `{{token}}` 时优先从 `environment` 读取，`collectionVariables` 单写不够，下游用例 header 取不到 token → 401。登录 + 探针 + 加购 + 结算的 Tests 脚本必须 `pm.collectionVariables.set(...)` + `pm.environment.set(...)` 双写。`basketId` / `orderNumber` / `skuId` / `prodId` 都走这个模式。
- **SMS 短信期望 `!='00000'`（反例 PASS）**：D4 v2.1 期望 `'00000'` 是错的 — mall4j 默认 SMS 服务关闭，发短信必返 `'A00001'`。v3.0 改成 `pm.expect(String(j.code)).to.not.eql('00000')`，验证"业务异常被正确返回"是测试目标本身。
- **6 folder 拆分（不是 5 或 7）**：1 公开接口 → 2 登录/认证 → 3 购物车（探针 + 加购）→ 4 订单（依赖 basketId）→ 5 支付（依赖 orderNumber，独立拆出）→ 6 鉴权/异常/边界（跨链路负面用例）。D4 把支付塞 Folder 4 子分组，链路顺序模糊；v3.0 把 Folder 5 独立后，cart→order→pay 链路一目了然。
- **path 变量 ≠ query 参数**：L4.6 取消订单 `MyOrderController.cancel` 是 `@PathVariable orderNumber`，正确 URL `{{base_url}}/p/myOrder/cancel/{{orderNumber}}`；写 `?orderNumber=X` 是 query，D5 用 `URL` 字段而非 `query` 字段填入。
- **DELETE 方法 body 用 raw JSON**：L3.5 删除购物车 `ShopCartController.deleteItem` 接收 `@RequestBody List<Long>`，body 是 raw JSON 数组 `[basketId]`，不能用 `application/x-www-form-urlencoded`；v3.0 headers 用 `Content-Type: application/json`。
- **未登录用例 pre-request 清 token**：跑完 L2.1 登录后 token 已写入 environment，跑 L6.1 "未登录访问用户信息-期望 401" 时如果不 unset，Authorization header 会自动填 token，期望 `A00004` 拿不到。pre-request 调 `pm.collectionVariables.unset('token') + pm.environment.unset('token') + Authorization header 显式空字符串`。
- **降级路径 30-34 PASS（不注 fixture）**：D5 v3.0 即使不注 `evidence/cart-fixture.sql` 也能跑，探针机制让"零 fixture 启动"成为可能 — 用户启 8086 后预计 30-34 PASS；要 38-40 PASS 黄金路径需另注 fixture + 启 admin 8085。

## 含义（用户能向面试官讲清楚什么）
- "为什么 v3.0 要在 collection 内置探针，不写 SQL 预填"：SQL fixture 有 3 个硬伤 — ① 跨环境难复制（dev/staging/prod 各一份）② 数据漂移（SKU 库存变 → SQL 失效）③ 用户首次跑要前置 SQL；探针让 collection 自包含，每次跑都拿最新数据库状态，零外部依赖 + 降级友好（探针失败时 fallback 到 env 默认值）。
- "为什么业务码断言用字符串而不是 200"：mall4j 复用 HTTP 200 表示"服务没崩"，业务正误用自定义 `code` 字段（`'00000'`=成功 / `'Axxxx'`=业务分类）；`ServerResponseEntity.code` 字段 Java 类型是 `String` 不是 `Integer`，JSON 序列化保留字符串。测试岗必须能区分 HTTP 状态码和业务码，`pm.expect(String(j.code))` 强制类型转换是正确写法。
- "为什么 v3.0 用 6 folder 不是 5 或 7"：5 folder 把支付塞进 Folder 4 子分组 → 链路顺序 cart→order→pay 模糊；7 folder 把鉴权拆成独立 folder → 鉴权 5 条 + 异常 8 条都是跨链路的负面用例，强行按 folder 切会让用例顺序乱跑（鉴权用例放在 Folder 3 会拿不到探针写回的 prodId/skuId）。6 folder 是"业务链路 5 + 跨链路负面 1"的最优切分。
- "为什么 SMS 用例期望 `!='00000'`"：测试用例期望值 = "业务行为是什么" 不是 "业务行为应该是什么"。mall4j 默认 SMS 服务关闭（dev profile 没配 SMS 厂商），发短信必返 `'A00001'`；期望 `'00000'` 是测不到真实业务行为，期望 `!='00000'` 才能验证"业务异常被正确处理"。这是"反例 PASS"设计 — 异常用例的 PASS 标准。
- "为什么 token 写回要双写 collectionVariables + environment"：Newman 是 Node 进程，`{{var}}` 模板解析在 collectionVariables 和 environment 两个作用域按优先级合并，header 引用 `{{token}}` 时优先 environment（Postman 官方规范）。单写 collectionVariables → header 拿不到 token → 401；双写 environment 是兜底 — 与 v2.1 fix 同源（沿用 D4 实跑教训）。
- "为什么 40 条用例分三种场景算 PASS"：黄金路径（启 8086 + 注 fixture + 启 admin）38-40 PASS / 降级路径（仅探针，无 fixture）30-34 PASS / 失败路径（8086 未启）0 PASS（但鉴权 5 条靠 HTTP 401 仍能跑）。这不是"含糊"而是"诚实的分场景判定" — 写简历时强调"骨架 PASS + 业务链路依赖前置数据 ready"，不写"全部通过"也不写"全部失败"。
- "黄金路径下 38-40 PASS 怎么算出来的"：40 总数 - L4.7 确认收货（依赖 admin 8085 发货，1 条） - L6.6 跨用户查订单（依赖 SQL 注 O9999_OTHER_USER，1 条） = 38 稳定 PASS；L6.7 跨用户改地址（依赖 SQL 注 otherUserAddrId）若 fixture 已注入则 PASS，计 39-40。这 2-3 条"卡点用例"是 fixture 注入的明确目标，写在 `api-40-cases.md §2` 三场景表。
- "v3.0 collection vs v2.1 怎么写简历金句"：用"骨架 20 → 完整链路 40（×2） + 5 业务码模板（×2.5） + 探针机制（创新点）"三段式 — 数字 ×2 原则在 v3.0 完美落地：20→40 是测试广度翻倍，2→5 业务码模板是断言维度翻 2.5 倍，探针机制是设计创新点。比"写 40 条 Postman 用例"更有差异化。

**Status**: active

参见：`../lessons/0011-postman-full-chain.html` · `../reference/0011-full-chain-cheatsheet.html` · `../test-cases/postman/mall4j-api-collection.json` · `../test-cases/api-40-cases.md` · `../doc/3-API接口/M1-D5-001-impl-notes.md`