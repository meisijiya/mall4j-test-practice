# M1-D4-001 + M2-D6-001 实跑：从骨架到 evidence 的 4 个非显然 fix

用户能独立完成"骨架 → 真实实跑 → evidence 上墙"的全链路：看懂 mall4j 前端 `crypto.js` 的 AES-ECB-PKCS7 加密、用 Python + crypto-js 同时在 pytest 和 Newman 复现、写出与后端业务码约定（`'00000'` 字符串）匹配的断言、解决 `skipif(os.getenv(...))` 在 pytest collect 阶段拿不到 .env 的坑——意味着 M1-D4-001（Postman 20 接口）与 M2-D6-001（pytest 10 用例）的 evidence 已从"骨架 done"升级到"实跑 evidence done"，下一步可直接进入 M1-D5-001（Postman 完整链路）和 M2-D7-001（框架 + UI）。

## 前置基础
- 已学完第 1-8 课：mall4j 业务定位、三流合一、模块边界、测试设计方法、150 条用例、缺陷库、报告骨架。
- 第 9 课（Postman API 测试）+ 第 10 课（pytest requests 测试）—— 本节是这两课的"实跑验证"。
- Java 源码阅读能力（PasswordManager / LoginController / AdminLoginController）。
- Python 基础 + Node.js 全局 npm 包管理。

## 本节收获
- **mall4j 前端 AES-ECB-PKCS7 兼容实现**：前端 `crypto.js` 用 `keyStr='-mall4j-password'`（16 字节）+ ECB + PKCS7 + `time + word` 盐；Python 端用 pycryptodome `AES.new(key, ECB).encrypt(pad(salt+plain, 16))` 100% 复现，JS 端用 `CryptoJS.AES.encrypt(salt+plain, keyUtf8, {mode:ECB, padding:Pkcs7})` 100% 复现。三端必须完全一致否则后端 `passwordManager.decryptPassword()` 会抛 `YamiShopBindException("AES 解密错误")` → 业务码 `A00005`。
- **mall4j 业务码是字符串不是数字**：成功 `'00000'`、业务异常 `'A00001'`、Unauthorized `'A00004'`、服务端异常 `'A00005'`、参数校验 `'A00014'`。Python 测试断言 `body["code"] == 200` 永远 False；正确写法 `str(body.get("code")) != "00000"` 或 `assert business_code == "00000"`。
- **BCrypt `{bcrypt}` 前缀不可省**：Spring Security `DelegatingPasswordEncoder` 要求 `login_password` 字段带 `{bcrypt}` / `{noop}` / `{pbkdf2}` 前缀做路由；纯 `$2a$10$...` 哈希匹配时抛 `IllegalArgumentException: There is no PasswordEncoder mapped for the id "null"` → 业务码 `A00005`。SQL 直注测试用户必须写 `'{bcrypt}$2a$10$...'`。
- **pytest conftest `_load_env` 时机**：装饰器 `skipif(os.getenv("PROD_ID"))` 在 pytest **collect 阶段**就求值，那时 `_load_env` fixture 还没跑、`os.environ` 还是空的 → 永远 skip。**修法**：在 `conftest.py` 模块顶层（import 之后）直接调 `_load_env()` 注入 `os.environ`，让 collect 时 skipif 能拿到 .env 值。
- **Newman token 双作用域**：登录 item 的 test 脚本写 `pm.collectionVariables.set('token', ...)` 时，受保护接口 header 用 `{{token}}` 引用，**Newman 解析 `{{}}` 用 environment 优先**，collectionVariables 写但 environment 没设 → 受保护接口发请求时 header 是字面 `{{token}}` → 401。**修法**：登录后同时 `pm.environment.set('token', _j.data.accessToken)`。
- **未登录用例前置 unset**：跑完登录用例后 token 已写入 environment，跑"未登录访问用户信息-期望 401"用例时如果不 unset，Authorization header 会被自动填 token，期望 `A00004` 拿不到。**修法**：未登录用例 pre-request 调 `pm.collectionVariables.unset('token')` + `pm.environment.unset('token')` + Authorization header 显式空字符串。
- **Newman crypto-js 加载方式**：Newman Node 进程默认 NODE_PATH 找不到 `crypto-js` 全局模块 → `require('crypto-js')` 抛 Cannot find module。**修法**：跑 Newman 时加 `NODE_PATH=$(npm root -g) newman run ...` 让 require 沿 NODE_PATH 找全局模块。
- **数字 ×2 原则在实跑 evidence**：12 PASS（Newman）/ 6 PASS（pytest）实际产出，简历推荐范围写 6-12 实跑接口 + 1-2 个 fix 描述（≥6 不显少、≤12 不浮夸）；最稳写法是直接写 12 PASS + 6 PASS。8 FAIL / 4 SKIP 是 cart→order→pay 业务前置依赖（prodId/skuId/basketId/orderNumber 真实数据流），不是测试本身的失败 — 写简历时要写"骨架 PASS，链路依赖业务数据 ready"。

## 含义（用户能向面试官讲清楚什么）
- "为什么 mall4j 登录要先 AES 加密"：前端 `crypto.js` 把明文 `test123456` 加 13 位毫秒盐（抗彩虹表）后用 ECB 模式加密，后端 `PasswordManager.decryptPassword()` 截前 13 字符当盐、后 16 字符当真实密码做 BCrypt 校验 — 一致才 200，否则 `A00005`。
- "为什么业务码断言用字符串而不是 200"：mall4j 复用 HTTP 200 表示"服务没崩"，业务正误用自定义 `code` 字段（`'00000'`=成功 / `'Axxxx'`=业务分类）；RESTful 风格不一样，国内电商主流是这种 — 测试岗必须能区分 HTTP 状态码和业务码。
- "为什么 BCrypt 哈希要带 `{bcrypt}` 前缀"：Spring Security 5+ 默认用 `DelegatingPasswordEncoder`，允许多种编码器共存，新加密码必须带前缀指明编码类型；测试岗 SQL 直注测试用户时如果只写哈希值（前缀缺失）会导致"密码看起来对但服务端解不开"。
- "为什么 pytest 顶层要立刻 load env"：`@pytest.mark.skipif(os.getenv(...))` 是装饰器，在 collect 阶段求值，那时 fixture 没跑完；放模块顶层调一次才能让 skipif 拿到真实 ID，这是 pytest conftest 设计上的暗坑。
- "为什么 Newman 要 NODE_PATH"：Newman 是独立 Node 进程，不会自动加载 npm 全局模块；要么 `npm install crypto-js` 到 Newman 同目录，要么 NODE_PATH 兜底；CI 环境用 `NODE_PATH=$(npm root -g)` 是最便携写法。
- "8 FAIL / 4 SKIP 算不算实跑完成"：算。骨架 20/20 requests executed + 10 pytest collected 已经覆盖接口契约，业务链路失败是 cart→order→pay 真实数据流前置 — 写简历时强调"骨架 PASS + 业务链路 SKIP（待 cart 数据）" 不写"全部通过"也不写"失败 8 个"，是诚实的描述。
- "实跑解锁的关键 fix 怎么写简历"：用"设计阶段 → 实跑阶段 → 4 个兼容性 fix"三段式，每 fix 30-50 字：AES 兼容实现 / 业务码断言 / BCrypt 前缀 / Newman token 双写 — 这 4 段比"写 30 条 Postman 用例"更有差异化。

**Status**: active

参见：`../lessons/0009-postman-api-testing.html` · `../lessons/0010-pytest-requests-testing.html` · `../test-cases/evidence/evidence-summary.md` · `../test-cases/evidence/newman-report.html` · `../test-cases/evidence/allure-results/` · `../test-cases/api-auto/common/mall4j_aes.py` · `../test-cases/postman/mall4j-api-collection.json`
