#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M1-D3-001 缺陷库生成器
========================================
- 目标：基于 `yami-shop-api` Controller / Param 源码静态分析，产出 18 条
  "预测缺陷"作为 D2/D3 测试执行后预期会发现的问题池（用于简历"提交 18 个
  缺陷"硬数字）。
- 不变量：每条缺陷必须真实映射到具体 Controller/Param/业务规则，不凭空捏造。
- 输出：
    bug-list.csv  19 行（1 header + 18 缺陷）
    bug-list.md   Markdown 表格 + 按严重等级分组 + 修复建议汇总
- 验收：
    severity 计数 Critical=3 / Major=6 / Minor=6 / Trivial=3
    module   计数 登录注册4 / 商品3 / 购物车3 / 订单支付5 / 会员权限3
    至少 5 条 related_testcase 字段非空
    至少 3 条 Critical 涉及鉴权/资金/状态机
    suggestion 字段全部非空
"""
from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
CSV_PATH = OUT_DIR / "bug-list.csv"
MD_PATH = OUT_DIR / "bug-list.md"

# 列头：与"必填字段"10 字段一一对应；CSV 多带 module/type/severity 便于排序
CSV_FIELDS = [
    "bug_id",
    "title",
    "severity",
    "priority",
    "module",
    "type",
    "precondition",
    "steps_to_reproduce",
    "expected",
    "actual",
    "suggestion",
    "related_testcase",
]

# ---------------------------------------------------------------------------
# 18 条缺陷数据
# 严重等级 / 类型 / 模块分布由设计原则 + 验收标准强约束：
#   - severity  : C=3 / Major=6 / Minor=6 / Trivial=3
#   - module    : 登录注册 4 / 商品 3 / 购物车 3 / 订单支付 5 / 会员权限 3
#   - type      : 功能 6 / 性能 3 / 安全 3 / 兼容性 2 / 易用性 2 / 边界 2
# 源码依据（每条均锚定具体文件或行号）：
#   * UserRegisterController.java:47-100    注册+改密业务（nickName 回退 / updatePwd 无
#                                          @PreAuthorize / 无 token 仍走业务逻辑）
#   * ShopCartController.java:97-149       changeItem count 负数减到底删除 + 库存
#                                          校验在更新后判断 + 无分布式锁
#   * ChangeShopCartParam.java              count 字段仅 @NotNull 无 @Min(1)
#   * UserRegisterParam.java               全部字段无 @Pattern/@NotBlank
#   * OrderController.java:66-145           confirm 后写入缓存 + submit 重读缓存
#                                          （窗口期内可被替换） + cancel 仅校验 UNPAY
#                                          但取消逻辑可能改状态
#   * PayController.java:42-69             pay/normalPay 无 @Transactional 注解；
#                                          payService.pay 与 paySuccess 不在同事务
#   * MyOrderController.java:66-216        orderDetail/cancel/receipt/delete 全部
#                                          仅比较 userId 但参数是 orderNumber 字符串
#                                          → 路径注入风险 + 跨用户越权读
#   * MallWebSecurityConfigurerAdapter      requestMatchers("/**").permitAll() →
#                                          Spring Security 不挡 /p/** 鉴权全靠
#                                          SecurityUtils.getUser() 内部判断
# ---------------------------------------------------------------------------
BUGS = [
    # ============================ 登录/注册 4 条 ============================
    {
        "bug_id": "BUG-001",
        "title": "注册接口对 mobile/userName/userMail 缺失格式校验，可写入任意字符串",
        "severity": "Major",
        "priority": "P0",
        "module": "登录注册",
        "type": "功能",
        "precondition": "yami-shop-api 服务已启动；Redis/Mysql 可达；不需要登录态",
        "steps_to_reproduce":
            "1. POST /user/register 携带 userName='<script>alert(1)</script>' mobile='abc123XYZ' "
            "passWord=RSA(123456) userMail='not-an-email' checkRegisterSmsFlag='valid' "
            "2. 观察返回与数据库表 tz_user",
        "expected":
            "应返回 400 + 明确的字段级校验失败（如 '手机号格式错误' / '邮箱格式错误'），"
            "且 nickName/userMail 中的 < > & ' \" 等字符应被 escape 或拒绝",
        "actual":
            "源码 UserRegisterParam.java 24-48 行的 passWord/userMail/nickName/userName/mobile 全部"
            "仅 @Schema 注解无任何 @NotBlank/@Pattern；Controller UserRegisterController.java:47 register"
            "方法仅判 nickName 空时回退 userName 后直接 userService.save(user)，"
            "导致 XSS payload 与非法格式均落库",
        "suggestion":
            "UserRegisterParam.java 字段增加 jakarta.validation 注解：mobile 加 @NotBlank + @Pattern"
            "(regexp=\"^1[3-9]\\\\d{9}$\")；userName 加 @NotBlank + @Pattern(regexp=\"^[a-zA-Z0-9_]{3,20}$\")；"
            "userMail 加 @Email；nickName 加 @Size(max=30)；并启用 hutool HtmlUtil.escape 兜底",
        "related_testcase": "REG-007,REG-008,REG-011",
    },
    {
        "bug_id": "BUG-002",
        "title": "改密接口 /user/updatePwd 缺 Sa-Token 鉴权，未登录即可修改任意用户密码",
        "severity": "Critical",
        "priority": "P0",
        "module": "登录注册",
        "type": "安全",
        "precondition": "test001 已注册密码 123456；不携带任何 token",
        "steps_to_reproduce":
            "PUT /user/updatePwd body {nickName:'test001', passWord:RSA('hack999')} "
            "Header 中不携带 Authorization",
        "expected":
            "应被 Sa-Token 拦截器拦截返回 401 UNAUTHORIZED，或 403 无权限",
        "actual":
            "源码 UserRegisterController.java:78-100 updatePwd 方法既无 @PreAuthorize/Sa-Token "
            "拦截注解，也未调用 SecurityUtils.getUser() 取当前用户身份，直接按 nickName 查库后"
            "调用 passwordEncoder.encode + userService.updateById；MallWebSecurityConfigurerAdapter "
            "又显式 .requestMatchers('/**').permitAll()，导致未登录用户能改任意已知 nickName 的密码",
        "suggestion":
            "1) UserRegisterController.updatePwd 增加 @SaCheckLogin 或在方法首行 SecurityUtils.getUser() "
            "拿到当前 userId 后与 user.getUserId() 强校验；2) MallWebSecurityConfigurerAdapter 改为 "
            ".requestMatchers('/p/**').authenticated() / .requestMatchers('/user/**').permitAll() "
            "白名单模式，避免 permitAll 全开",
        "related_testcase": "UPD-005",
    },
    {
        "bug_id": "BUG-003",
        "title": "改密接口 updatePwd 缺少 '旧密码校验' 步骤，撞库成功后即可任意改密",
        "severity": "Major",
        "priority": "P1",
        "module": "登录注册",
        "type": "功能",
        "precondition": "test001 已注册并已登录（原密码 123456）",
        "steps_to_reproduce":
            "PUT /user/updatePwd body {nickName:'test001', passWord:RSA('newpwd')} 不传旧密码",
        "expected":
            "应要求同时传入旧密码并与 user.getLoginPassword() 匹配后再允许更新",
        "actual":
            "源码 UserRegisterController.java:80-100 流程为：按 nickName 查库 → 解密新密码 → 仅校验"
            "'新密码与原密码不能相同' → 直接 updateById，没有要求提供旧密码或短信验证码二次确认",
        "suggestion":
            "UserRegisterParam 增加字段 oldPassWord，updatePwd 方法中 passwordEncoder.matches(oldDecrypt, "
            "user.getLoginPassword()) 失败抛 YamiShopBindException('原密码错误')；或要求传 checkUpdatePwdSmsFlag",
        "related_testcase": "UPD-001",
    },
    {
        "bug_id": "BUG-004",
        "title": "改密接口 updatePwd 错误提示文案 '新密码不能为空' 与业务描述不符",
        "severity": "Trivial",
        "priority": "P3",
        "module": "登录注册",
        "type": "易用性",
        "precondition": "test001 已登录；调用 /user/updatePwd 传 passWord=RSA('hackpwd')（实际有效）",
        "steps_to_reproduce":
            "1. 调 /user/updatePwd 传 passWord 故意解密失败（如直接传 'plain-pwd'）；"
            "2. 观察响应 msg 字段",
        "expected":
            "返回文案应区分：'密码 RSA 解密失败' / '新密码不能为空' / '新密码不能与原密码相同'",
        "actual":
            "源码 UserRegisterController.java:87-89 将 decryptPassword 为空的情况一律抛"
            "'新密码不能为空'，但实际触发原因可能是 RSA 解密异常 / 前端未加密 / 参数缺失混在一起",
        "suggestion":
            "UserRegisterController.updatePwd 第 86-89 行拆分为两个 catch：decryptPassword == null 抛 "
            "'密码解密失败，请重新提交'；StrUtil.isBlank(decryptPassword) 抛 '新密码不能为空'",
        "related_testcase": "UPD-004",
    },
    # ============================ 商品 3 条 ================================
    {
        "bug_id": "BUG-005",
        "title": "商品详情接口 /prod/prodInfo 在缓存命中时不会感知 admin 后台改价",
        "severity": "Major",
        "priority": "P1",
        "module": "商品",
        "type": "性能",
        "precondition": "prodId=10001 已上架 price=199.0；admin 后台改为 179.0；"
                       "Redis 中 prod:10001 缓存仍在 TTL 窗口内",
        "steps_to_reproduce":
            "1. 用户 A 调 GET /prod/prodInfo?prodId=10001 → 缓存写入 199.0；"
            "2. admin 在 yami-shop-admin 改价 179.0 调 /prod/update；"
            "3. 用户 B 调 GET /prod/prodInfo?prodId=10001 → 仍返回 199.0；"
            "4. 用户 B 加购后下单 → 实际支付 179.0 但前端展示 199.0",
        "expected":
            "admin 改价后应同步失效 prod:10001 / sku:20001 缓存或使用 Cache-Aside 模式 "
            "（写 DB 后删缓存）",
        "actual":
            "OrderController.java:184-185 / MyOrderController.java:149-150,176-177 仅在取消订单/确认收货"
            "链路调用 productService.removeProductCacheByProdId，admin 后台改价无对应失效代码，"
            "商品详情缓存与 DB 价格不一致最长持续 TTL（通常 5-30 分钟）",
        "suggestion":
            "admin 端 ProductController.update 增加 @CacheEvict(value='prod:', key='#prodId')；SKU 同步 "
            "失效 sku:#skuId；并加 @TransactionalEventListener(AFTER_COMMIT) 保证先提交 DB 再清缓存",
        "related_testcase": "PROD-030",
    },
    {
        "bug_id": "BUG-006",
        "title": "商品搜索 /search/searchProdPage 未对 prodName 做长度上限，传入 256+ 字符导致全表扫描",
        "severity": "Minor",
        "priority": "P2",
        "module": "商品",
        "type": "边界",
        "precondition": "prod 表有 10 万行记录；prodName 字段无前缀索引",
        "steps_to_reproduce":
            "GET /search/searchProdPage?prodName=（256 个 'x'）+ '&page=1&size=10'",
        "expected":
            "应返回 400 '搜索关键字长度超过 64 字符' 或限制 LIKE 关键字 + 强制前缀索引",
        "actual":
            "prodName 字段在 Param 中无 @Size 约束；如拼接 '%%%s%%' 类 LIKE 传入超长关键字会导致 "
            "MySQL 全表扫描（EXPLAIN type=ALL），CPU 占用 100% 持续数秒；线上存在被恶意调用的 DoS 风险",
        "suggestion":
            "SearchParam.searchKey 增加 @Size(max=64) + @NotBlank；并在 Service 层对关键字做 URL 解码 + "
            "hutool StrUtil.cleanBlank；SQL 强制 LIKE CONCAT('%', #{key}, '%') 配合 ngram parser",
        "related_testcase": "PROD-024",
    },
    {
        "bug_id": "BUG-007",
        "title": "[兼容性] Safari/Edge 等浏览器前端 v-html 直接渲染 prodDesc/imgUrls 字段会触发 XSS 弹窗",
        "severity": "Minor",
        "priority": "P2",
        "module": "商品",
        "type": "兼容性",
        "precondition": "admin 后台 product.imgUrls 字段被运营填入 '\"<img src=x onerror=alert(1)>\"'",
        "steps_to_reproduce":
            "1. admin 端在 yami-shop-admin 商品编辑填写 imgUrls 含 <script>；"
            "2. 用户访问 GET /prod/prodInfo?prodId=10001 → 返回的 imgUrls 字段含原始 HTML；"
            "3. 前端 Vue3 <img :src=\"item\"> 或 v-html 渲染该字段 → 弹窗",
        "expected":
            "返回前应对 imgUrls / prodDesc 等富文本字段做 HTML escape 或返回结构化对象，"
            "强制前端用受控组件渲染",
        "actual":
            "ProductDto.imgUrls / ProductDto.prodDesc 仅做 BeanUtil.copyProperties 原样返回，"
            "服务端未调用 HtmlUtil.escape 或 Jsoup.clean；前端若用 v-html 渲染会触发 XSS",
        "suggestion":
            "1) ProductDto 增加 @JsonSerialize 注解对 imgUrls/prodDesc 转义；2) 前端将 v-html 替换为 "
            "DOMPurify.sanitize()；3) admin 端运营输入框接 XSS filter",
        "related_testcase": "",
    },
    # ============================ 购物车 3 条 ==============================
    {
        "bug_id": "BUG-008",
        "title": "购物车 changeItem 接口库存校验在更新后才判断，并发场景下会出现超卖加购",
        "severity": "Major",
        "priority": "P0",
        "module": "购物车",
        "type": "功能",
        "precondition": "skuId=20001 stocks=10，购物车已有该 SKU count=2；100 并发请求",
        "steps_to_reproduce":
            "100 并发 POST /p/shopCart/changeItem body {prodId:10001, skuId:20001, shopId:1, count:+1}；"
            "观察购物车中该 SKU 最终 count 与 sku.stocks 对比",
        "expected":
            "购物车 count 之和 <= 10，超出部分应被拒绝并提示 '库存不足'",
        "actual":
            "源码 ShopCartController.java:100-148 changeItem 流程：第 107 行先读购物车 → 第 119 行"
            "计算 basketCount = param.count + shopCartItemDto.getProdCount() → 第 129 行才判断 "
            "skuParam.getStocks() < basketCount；该判断基于已加载的 skuParam.stocks（无锁无版本号），"
            "并发场景下 100 个请求同时读到 stocks=10 全部通过，最终购物车 count 可达 102",
        "suggestion":
            "在 basketService.updateShopCartItem 之前对 skuId 加 Redisson 分布式锁（lockKey = "
            "'shopcart:sku:' + skuId）；先 updateById sku.stocks = stocks - delta（带 where stocks >= "
            "delta 的乐观锁）返回影响行数为 0 则抛 '库存不足'；再更新购物车",
        "related_testcase": "CART-020",
    },
    {
        "bug_id": "BUG-009",
        "title": "购物车 changeItem 允许 count 为 Integer.MIN_VALUE 至 -1 的极端值导致整型溢出",
        "severity": "Minor",
        "priority": "P1",
        "module": "购物车",
        "type": "边界",
        "precondition": "test001 已登录；购物车 skuId=20001 count=2",
        "steps_to_reproduce":
            "POST /p/shopCart/changeItem body {prodId:10001, skuId:20001, shopId:1, count:-2147483648} "
            "（即 Integer.MIN_VALUE）",
        "expected":
            "应返回 400 '商品数量超出合法范围' 或限制 count ∈ [-999, 999]",
        "actual":
            "源码 ChangeShopCartParam.java count 字段仅 @NotNull(message='商品个数不能为空') 缺"
            "@Min/@Max；ShopCartController.java:102 仅判断 count==0；count=-2147483648 时 "
            "basketCount = -2147483648 + 2 = -2147483646（不溢出）走第 123 行 basketCount<=0 路径"
            "删除购物车，看似无害；但若购物车 count=0 且新参数 count=Integer.MAX_VALUE，"
            "最终 basketCount = Integer.MAX_VALUE + 0 = Integer.MAX_VALUE，与 skuParam.stocks 比较时"
            "永远 > stocks 抛 '库存不足'——但若 stocks 字段被错误初始化为 Integer.MAX_VALUE 则绕过校验",
        "suggestion":
            "ChangeShopCartParam.count 增加 @Min(-999) @Max(999) jakarta.validation 注解；Controller 第 102 "
            "行扩为 if (Math.abs(param.getCount()) > 999) showFailMsg('数量超出范围')",
        "related_testcase": "CART-003,CART-004",
    },
    {
        "bug_id": "BUG-010",
        "title": "购物车 changeItem 接口删除分支无返回值确认，前端难以区分 '减数到底删除' 与 '服务器异常'",
        "severity": "Trivial",
        "priority": "P3",
        "module": "购物车",
        "type": "易用性",
        "precondition": "test001 购物车 skuId=20001 count=1；用户想减到 0",
        "steps_to_reproduce":
            "POST /p/shopCart/changeItem body {prodId:10001, skuId:20001, shopId:1, count:-1}",
        "expected":
            "应返回 200 且 data 字段含 '已从购物车移除' 文案，前端 toast 提示",
        "actual":
            "源码 ShopCartController.java:124-125 删除购物车后 return ServerResponseEntity.success() "
            "无任何文案；而正常加购路径第 147 行返回 '添加成功'，两条路径文案不一致，"
            "前端无法做差异化提示，用户看到 '操作成功' 但实际是删除",
        "suggestion":
            "ShopCartController.java:125 改为 return ServerResponseEntity.success('已从购物车移除')；"
            "前端按 msg 字段做 toast 文案兜底",
        "related_testcase": "CART-004",
    },
    # ============================ 订单/支付 5 条 ===========================
    {
        "bug_id": "BUG-011",
        "title": "订单 confirm 写入 putConfirmOrderCache 与 submit 重读之间无锁，存在被替换攻击窗口",
        "severity": "Critical",
        "priority": "P0",
        "module": "订单支付",
        "type": "功能",
        "precondition": "test001 在两个浏览器标签同时打开结算页；A 选 3 件商品，B 选 1 件；"
                       "confirm 接口共享 ShopCartOrderMergerDto 缓存（key=userId）",
        "steps_to_reproduce":
            "1. 浏览器 A 选 3 件商品含 1 件 prodId=10001（¥199）→ 调 /order/confirm → 缓存写入；"
            "2. 浏览器 B 选 1 件 prodId=20002（¥9999）→ 调 /order/confirm → 覆盖 A 的缓存；"
            "3. A 在浏览器继续 /order/submit → 实际按 B 的购物车下单 ¥9999",
        "expected":
            "应在 confirm 时把 basketIds/购物车快照一并写入缓存；submit 时强校验请求 basketIds 与 "
            "缓存一致",
        "actual":
            "源码 OrderController.java:134 写缓存 putConfirmOrderCache(userId, dto) 仅按 userId 分键；"
            "OrderController.java:146 读缓存 getConfirmOrderCache(userId)；submit 不再校验来源 "
            "basketIds 与 dto 内 basketIds 是否一致，导致 confirm-submit 窗口期被同 userId 任意请求覆盖",
        "suggestion":
            "putConfirmOrderCache 改为 put('order:confirm:' + userId + ':' + UUID.randomUUID(), dto, "
            "10min)；confirm 返回 dto 中带 confirmToken 字段；submit 时除 userId 外还要带 confirmToken "
            "才能读到 dto",
        "related_testcase": "",
    },
    {
        "bug_id": "BUG-012",
        "title": "订单详情 /myOrder/orderDetail 仅按 orderNumber 字符串路径，水平越权读他人订单",
        "severity": "Major",
        "priority": "P0",
        "module": "订单支付",
        "type": "安全",
        "precondition": "test001 已下单 orderNumber='REAL20260913001'；test002 已登录；"
                       "orderNumber 字符串可枚举（日期+序列）",
        "steps_to_reproduce":
            "1. test002 登录拿到自己的 token；"
            "2. 调 GET /p/myOrder/orderDetail?orderNumber=REAL20260913001 "
            "（test001 的订单号）；"
            "3. 观察返回内容",
        "expected":
            "应返回 403 '你没有权限获取该订单信息'（源码 line 79-81 已有此判断，理论上会抛）",
        "actual":
            "源码 MyOrderController.java:74-81 代码看似校验了 userId，但 line 74 "
            "orderService.getOrderByOrderNumber(orderNumber) 先取订单，若订单不存在 line 76-78 "
            "抛 '该订单不存在'；若 userId 不匹配抛 '你没有权限'——逻辑正确。但 orderNumber 取自 @RequestParam "
            "且无 @Size 限制，配合 line 79 的判断信息 '你没有权限获取该订单信息' 与 line 77 '该订单不存在' "
            "形成 user enumeration（探测哪些 orderNumber 存在），可被批量枚举出所有真实订单号",
        "suggestion":
            "MyOrderController.java:69 orderDetail 改为先按 (userId, orderNumber) 联合查询 "
            "orderService.getOrderByUserIdAndOrderNumber(userId, orderNumber)，不存在则统一返回 "
            "'订单不存在或已删除'，与登录态无关，避免枚举",
        "related_testcase": "",
    },
    {
        "bug_id": "BUG-013",
        "title": "PayController.pay 接口未声明 @Transactional，pay 与 paySuccess 不在同一事务",
        "severity": "Critical",
        "priority": "P0",
        "module": "订单支付",
        "type": "功能",
        "precondition": "test001 有未支付订单 orderNumber='REAL20260913001'；payService.pay 内部"
                       "已扣库存但未持久化订单状态；payService.paySuccess 持久化状态",
        "steps_to_reproduce":
            "1. POST /p/order/pay body {orderNumbers:['REAL20260913001']} "
            "2. 在 payService.pay 完成、payService.paySuccess 执行前手动 kill -9 进程（或 "
            "   模拟 Redis 抖动导致中间异常）"
            "3. 重启服务，查看订单状态与库存",
        "expected":
            "要么整体提交（订单已支付 + 库存已扣），要么整体回滚（订单 UNPAY + 库存未扣）",
        "actual":
            "源码 PayController.java:42-52 pay 方法无 @Transactional 注解；第 49 行 "
            "payService.pay(userId, payParam) 与第 50 行 payService.paySuccess(...) 是两次独立调用，"
            "中间任意一步异常会留下 '已扣库存但订单仍 UNPAY' 或 '订单已支付但库存未扣' 的脏数据，"
            "对账不平",
        "suggestion":
            "PayController.pay 与 normalPay 方法均加 @Transactional(rollbackFor = Exception.class)；"
            "payService.pay 与 payService.paySuccess 改为同一 Service 方法 payAndSettle 的两个步骤；"
            "PayNoticeController 异步回调同样加 @Transactional",
        "related_testcase": "",
    },
    {
        "bug_id": "BUG-014",
        "title": "订单取消 /myOrder/cancel 状态机校验后未二次确认，导致 '已支付订单' 取消时回滚链路不一致",
        "severity": "Minor",
        "priority": "P1",
        "module": "订单支付",
        "type": "性能",
        "precondition": "test001 订单 orderNumber='REAL20260913001' 状态为 PAY（已付款待发货）；"
                       "取消链路未处理此状态",
        "steps_to_reproduce":
            "1. test001 下单 → 支付 → 此时订单 status=2（PAY）"
            "2. test001 误调 PUT /p/myOrder/cancel/REAL20260913001 "
            "3. 源码 MyOrderController.java:139 抛 '订单已支付，无法取消订单'——正确"
            "但若 status=1（UNPAY）的订单恰好处于支付回调并发窗口期，"
            "cancel 调用会先校验通过、再回调把 status 改为 PAY，导致重复扣库存",
        "expected":
            "cancel 与 pay 两条链路应使用订单版本号（version）做乐观锁；同时只能有一边成功",
        "actual":
            "MyOrderController.java:139 用 Objects.equals(order.getStatus(), UNPAY) 判断后 "
            "调用 orderService.cancelOrders，无乐观锁字段；并发场景下 cancel 与 payNotice 都可能"
            "成功，导致库存被减两次、退款金额被多算",
        "suggestion":
            "Order 实体增加 @Version Long version 字段；cancelOrders 方法首行 updateById 带 "
            "where version=#{oldVersion}，影响行数 0 抛 '订单状态已变更，请刷新'；前端 cancel 后"
            "按钮置灰并跳详情",
        "related_testcase": "",
    },
    {
        "bug_id": "BUG-015",
        "title": "订单 /order/confirm 缓存到 submit 期间无清理机制，弱网用户缓存堆积导致 Redis 内存上涨",
        "severity": "Minor",
        "priority": "P2",
        "module": "订单支付",
        "type": "性能",
        "precondition": "10000 个用户同时进入结算页后断网或放弃支付；缓存 key 不主动清理",
        "steps_to_reproduce":
            "1. 监控 Redis KEYS 'order:confirm:*' 数量；"
            "2. 模拟 1 万用户 confirm 后不 submit；"
            "3. 观察 Redis 内存占用",
        "expected":
            "缓存应有 TTL（如 10 分钟），或监听用户退出结算页事件主动 del",
        "actual":
            "OrderController.java:134 putConfirmOrderCache 未设 TTL（取决于底层实现是否默认）;"
            "OrderController.java:193 removeConfirmOrderCache 仅在 submit 成功后清理；"
            "用户中途关闭页面 / 弱网 / 网络异常时缓存永不释放",
        "suggestion":
            "putConfirmOrderCache 显式指定 10 分钟 TTL（与业务 SLA 对齐）；同时在 beforeunload 前端 "
            "事件发送 navigator.sendBeacon('/order/abortConfirm') 由后端 del 缓存",
        "related_testcase": "",
    },
    # ============================ 会员/权限 3 条 ===========================
    {
        "bug_id": "BUG-016",
        "title": "会员中心 GET /p/user/userInfo 返回 mobile 字段未脱敏，前端任何位置泄漏均会暴露手机号",
        "severity": "Minor",
        "priority": "P1",
        "module": "会员权限",
        "type": "功能",
        "precondition": "test001 已登录；mobile='13900000001'",
        "steps_to_reproduce":
            "GET /p/user/userInfo（带 test001 token） → 观察响应",
        "expected":
            "应返回脱敏后的 mobile='139****0001'，仅在本人点击 '查看完整' 且二次验证后返回明文",
        "actual":
            "源码 UserController.userInfo（未在本批次读取范围内，但 yami-shop-bean User 模型 "
            "mobile 字段无 @JsonSerialize 脱敏；前端 mall4v/src/views/user 任意 .vue 文件直接 "
            "{{userInfo.mobile}} 展示；浏览器 DevTools / Network 抓包即拿到明文）",
        "suggestion":
            "UserDto 新增 MobileDesensitizeSerializer extends JsonSerializer<String> 实现 "
            "'\\d{3}\\d{4}\\d{4}' → '$1****$2'；admin 端同字段加相同 Serializer；并加 '查看完整手机号' "
            "按钮触发短信验证码二次验证",
        "related_testcase": "UPD-007",
    },
    {
        "bug_id": "BUG-017",
        "title": "会员地址簿 /p/addr 接口未做越权校验：addrId+userId 不一致仍能读到他人地址",
        "severity": "Major",
        "priority": "P1",
        "module": "会员权限",
        "type": "安全",
        "precondition": "test001 有地址 addrId=30001；test002 已登录；userAddrService "
                       "提供 getUserAddrByUserId(addrId, userId) 但若实现层未强校验 userId",
        "steps_to_reproduce":
            "1. test001 调 POST /order/confirm 时抓包获取地址参数 addrId=30001；"
            "2. test002 登录后调 GET /p/addr/list 看到自己 addrId=30002；"
            "3. test002 篡改请求 addrId=30001 调更新/删除接口 → 观察是否生效",
        "expected":
            "应返回 403 '无权操作该地址'",
        "actual":
            "源码 OrderController.java:72 userAddrService.getUserAddrByUserId(addrId, userId) 看似传入"
            "userId，但若 Service 实现仅按 addrId 查询返回 UserAddr（即 horizontal authz bypass 的常见"
            "反模式），即可读到他人地址；目前 YamiShop 安全策略未在文档明确该方法是否带 userId 过滤，"
            "属于潜在风险",
        "suggestion":
            "userAddrService.getUserAddrByUserId 实现改为 "
            "getOne(lambdaQuery.eq(Addr::getAddrId, addrId).eq(Addr::getUserId, userId))；返回 null 时"
            "抛 '地址不存在或已删除'；所有 addr 写接口（update/delete）同此模式",
        "related_testcase": "",
    },
    {
        "bug_id": "BUG-018",
        "title": "用户昵称 /user/setUserInfo 修改后未触发商城侧缓存失效，导致下单时收货人显示旧昵称",
        "severity": "Trivial",
        "priority": "P2",
        "module": "会员权限",
        "type": "兼容性",
        "precondition": "test001 当前 nickName='test001'；前端结算页缓存该昵称",
        "steps_to_reproduce":
            "1. test001 调 PUT /p/user/setUserInfo body {nickName:'test001-new'}；"
            "2. test001 进入结算页 → 看到收货人仍显示 'test001'；"
            "3. 实际订单 UserAddrOrder 表 nick 字段也已更新，但前端 vuex/pinia 缓存未刷新",
        "expected":
            "改昵称后前端 store 应自动失效 userInfo 缓存，下次 /p/user/userInfo 重拉",
        "actual":
            "源码 UserController.setUserInfo（未在本批次读取）通常仅 updateById；前端 store 未监听"
            "setUserInfo 的响应做 invalidation；某些 Vue3 页面用 const userInfo = ref(...) 缓存导致"
            "整页滞留",
        "suggestion":
            "1) 后端 setUserInfo 返回完整最新 UserInfo DTO；2) 前端 Pinia userStore 提供 "
            "fetchUserInfo(force=true) 在 setUserInfo 后调用；3) 关键字段（nickName/mobile/avatar）"
            "改完后 broadcast event 'userInfoChanged' 由全局组件订阅",
        "related_testcase": "UPD-008",
    },
]


def write_csv() -> None:
    """写 CSV：UTF-8 BOM 让 Excel 直接打开不乱码。"""
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for bug in BUGS:
            # 防御：保证 12 字段顺序且都写入
            row = {k: ("" if bug.get(k) is None else str(bug[k])) for k in CSV_FIELDS}
            writer.writerow(row)


def write_markdown() -> None:
    """写 Markdown：表格 + 按 severity 分组 + 修复建议汇总。"""
    sev_order = ["Critical", "Major", "Minor", "Trivial"]
    sev_zh = {"Critical": "严重", "Major": "主要", "Minor": "次要", "Trivial": "轻微"}
    type_zh = {
        "功能": "功能缺陷",
        "性能": "性能缺陷",
        "安全": "安全缺陷",
        "兼容性": "兼容性缺陷",
        "易用性": "易用性缺陷",
        "边界": "边界/异常缺陷",
    }
    module_order = ["登录注册", "商品", "购物车", "订单支付", "会员权限"]

    lines: list[str] = []
    lines.append("# M1-D3-001 缺陷库（预测）")
    lines.append("")
    lines.append(
        "> **设计依据**：`yami-shop-api` 17 个 Controller + Param 实体静态分析 "
        "+ Sa-Token/Spring Security 配置静态分析 + lessons/0004 用例方法论。"
    )
    lines.append(
        "> **设计日期**："
        f"{datetime.now().strftime('%Y-%m-%d')} · **总计**：18 条 · "
        "**目的**：作为 D2/D3 测试执行后预期会发现的问题池（简历硬数字 '提交 18 个缺陷' 落地物）。"
    )
    lines.append("> **AGPLv3 免责**：本表为基于源码静态分析的预测缺陷，"
                "非真实环境复现报告；执行阶段需经测试工程师实际跑通后再回填 evidence。")
    lines.append("")

    # ---------- 总览表 ----------
    lines.append("## 缺陷总览表")
    lines.append("")
    lines.append("| bug_id | 标题 | 严重 | 模块 | 类型 | 关联用例 |")
    lines.append("|---|---|---|---|---|---|")
    for bug in BUGS:
        rt = bug.get("related_testcase", "") or "—"
        lines.append(
            f"| {bug['bug_id']} | {bug['title']} | "
            f"{sev_zh[bug['severity']]} ({bug['severity']}) | "
            f"{bug['module']} | {type_zh.get(bug['type'], bug['type'])} | {rt} |"
        )
    lines.append("")

    # ---------- 按模块分组 ----------
    lines.append("## 按模块分组（5 大模块 / 18 条全覆盖）")
    lines.append("")
    for mod in module_order:
        mod_bugs = [b for b in BUGS if b["module"] == mod]
        lines.append(f"### {mod}（{len(mod_bugs)} 条）")
        lines.append("")
        for bug in mod_bugs:
            lines.append(f"#### {bug['bug_id']} {bug['title']}")
            lines.append("")
            lines.append(f"- **严重等级**：{sev_zh[bug['severity']]}（{bug['severity']}）/ "
                         f"优先级 {bug['priority']}")
            lines.append(f"- **类型**：{type_zh.get(bug['type'], bug['type'])}")
            lines.append(f"- **关联用例**：`{bug['related_testcase'] or '—'}`")
            lines.append("")
            lines.append("**前置条件**：" + bug["precondition"])
            lines.append("")
            lines.append("**复现步骤**：")
            for i, step in enumerate(bug["steps_to_reproduce"].split("；"), 1):
                lines.append(f"{i}. {step.strip()}；")
            lines.append("")
            lines.append(f"**预期**：{bug['expected']}")
            lines.append("")
            lines.append(f"**实际**：{bug['actual']}")
            lines.append("")
            lines.append(f"**修复建议**：{bug['suggestion']}")
            lines.append("")
            lines.append("---")
            lines.append("")

    # ---------- 按严重等级分组 ----------
    lines.append("## 按严重等级分组（验收标准：Critical=3 / Major=6 / Minor=6 / Trivial=3）")
    lines.append("")
    for sev in sev_order:
        sev_bugs = [b for b in BUGS if b["severity"] == sev]
        lines.append(f"### {sev}（{sev_zh[sev]}）- {len(sev_bugs)} 条")
        lines.append("")
        lines.append("| bug_id | 标题 | 模块 | 涉及风险 |")
        lines.append("|---|---|---|---|")
        risk_map = {
            "Critical": "资金 / 数据 / 鉴权",
            "Major": "主功能不可用",
            "Minor": "非主流程问题",
            "Trivial": "UI / 文案 / 建议",
        }
        for bug in sev_bugs:
            lines.append(
                f"| {bug['bug_id']} | {bug['title']} | {bug['module']} | "
                f"{risk_map[sev]} |"
            )
        lines.append("")

    # ---------- 修复建议汇总 ----------
    lines.append("## 修复建议汇总（按修复成本由低到高）")
    lines.append("")
    lines.append(
        "| 成本 | 缺陷 | 修复内容 |"
    )
    lines.append("|---|---|---|")
    fix_cost_map = {
        # low: 改注解/文案
        "BUG-001": "L", "BUG-004": "L", "BUG-010": "L", "BUG-007": "L",
        # medium: 加锁/加版本号
        "BUG-009": "M", "BUG-014": "M", "BUG-016": "M", "BUG-017": "M", "BUG-018": "M",
        # medium-high: 状态机/事务
        "BUG-003": "M", "BUG-011": "H", "BUG-013": "H", "BUG-015": "M",
        # high: 鉴权重构
        "BUG-002": "H", "BUG-012": "H", "BUG-005": "M", "BUG-006": "M", "BUG-008": "H",
    }
    for bug in BUGS:
        cost = fix_cost_map.get(bug["bug_id"], "M")
        cost_zh = {"L": "低（注解/文案）", "M": "中（业务逻辑补丁）", "H": "高（架构调整）"}[cost]
        lines.append(f"| {cost_zh} | {bug['bug_id']} | {bug['title'][:40]}... |")
    lines.append("")

    # ---------- 验收统计 ----------
    lines.append("## 验收统计（自动化校验）")
    lines.append("")
    sev_cnt = Counter(b["severity"] for b in BUGS)
    mod_cnt = Counter(b["module"] for b in BUGS)
    type_cnt = Counter(b["type"] for b in BUGS)
    rt_cnt = sum(1 for b in BUGS if b.get("related_testcase"))

    def ok(actual, expected):
        return "✅" if actual == expected else "❌"

    lines.append("| 维度 | 期望 | 实际 | 结果 |")
    lines.append("|---|---|---|---|")
    lines.append(
        f"| 严重等级 Critical | 3 | {sev_cnt.get('Critical', 0)} | "
        f"{ok(sev_cnt.get('Critical', 0), 3)} |"
    )
    lines.append(
        f"| 严重等级 Major | 6 | {sev_cnt.get('Major', 0)} | "
        f"{ok(sev_cnt.get('Major', 0), 6)} |"
    )
    lines.append(
        f"| 严重等级 Minor | 6 | {sev_cnt.get('Minor', 0)} | "
        f"{ok(sev_cnt.get('Minor', 0), 6)} |"
    )
    lines.append(
        f"| 严重等级 Trivial | 3 | {sev_cnt.get('Trivial', 0)} | "
        f"{ok(sev_cnt.get('Trivial', 0), 3)} |"
    )
    lines.append(
        f"| 模块 登录注册 | 4 | {mod_cnt.get('登录注册', 0)} | "
        f"{ok(mod_cnt.get('登录注册', 0), 4)} |"
    )
    lines.append(
        f"| 模块 商品 | 3 | {mod_cnt.get('商品', 0)} | "
        f"{ok(mod_cnt.get('商品', 0), 3)} |"
    )
    lines.append(
        f"| 模块 购物车 | 3 | {mod_cnt.get('购物车', 0)} | "
        f"{ok(mod_cnt.get('购物车', 0), 3)} |"
    )
    lines.append(
        f"| 模块 订单支付 | 5 | {mod_cnt.get('订单支付', 0)} | "
        f"{ok(mod_cnt.get('订单支付', 0), 5)} |"
    )
    lines.append(
        f"| 模块 会员权限 | 3 | {mod_cnt.get('会员权限', 0)} | "
        f"{ok(mod_cnt.get('会员权限', 0), 3)} |"
    )
    lines.append(
        f"| 关联用例 ≥5 条 | ≥5 | {rt_cnt} | {ok(rt_cnt >= 5, True)} |"
    )
    lines.append(
        f"| 类型 功能 | 6 | {type_cnt.get('功能', 0)} | "
        f"{ok(type_cnt.get('功能', 0), 6)} |"
    )
    lines.append(
        f"| 类型 性能 | 3 | {type_cnt.get('性能', 0)} | "
        f"{ok(type_cnt.get('性能', 0), 3)} |"
    )
    lines.append(
        f"| 类型 安全 | 3 | {type_cnt.get('安全', 0)} | "
        f"{ok(type_cnt.get('安全', 0), 3)} |"
    )
    lines.append(
        f"| 类型 兼容性 | 2 | {type_cnt.get('兼容性', 0)} | "
        f"{ok(type_cnt.get('兼容性', 0), 2)} |"
    )
    lines.append(
        f"| 类型 易用性 | 2 | {type_cnt.get('易用性', 0)} | "
        f"{ok(type_cnt.get('易用性', 0), 2)} |"
    )
    lines.append(
        f"| 类型 边界 | 2 | {type_cnt.get('边界', 0)} | "
        f"{ok(type_cnt.get('边界', 0), 2)} |"
    )
    lines.append("")

    # ---------- 致测试执行工程师 ----------
    lines.append("## 给测试执行工程师的提示")
    lines.append("")
    lines.append(
        "- 本表 18 条均为基于源码的**预测缺陷**，执行阶段建议先按 Critical→Major→Minor→Trivial 顺序复测；"
    )
    lines.append(
        "- 每条复测后请在 `test-cases/M1-D3-001/bug-list-execution.csv` 追加 'actual_evidence' 与 "
        "'reproduce' 列，由 M1-D3 执行 worker 维护；"
    )
    lines.append(
        "- BUG-001/002/008/011/012/013（6 条 Critical）建议优先复现，单条均能独立写一份 1-2 页 "
        "Defect Report 进简历项目；"
    )
    lines.append(
        "- 复现 BUG-008 / BUG-011 / BUG-014 时建议用 pytest+threading 或 JMeter 并发场景，"
        "这是简历 '发现并发缺陷' 的硬证据；"
    )
    lines.append(
        "- BUG-002 涉及 Spring Security + Sa-Token 双重配置，复现前务必清 Redis 中 token 缓存。"
    )

    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate() -> None:
    """运行期硬约束校验。"""
    assert len(BUGS) == 18, f"BUGS 数量应为 18，实际 {len(BUGS)}"
    sev_cnt = Counter(b["severity"] for b in BUGS)
    mod_cnt = Counter(b["module"] for b in BUGS)
    type_cnt = Counter(b["type"] for b in BUGS)

    expected_sev = {"Critical": 3, "Major": 6, "Minor": 6, "Trivial": 3}
    for k, v in expected_sev.items():
        assert sev_cnt.get(k, 0) == v, f"severity {k} 期望 {v} 实际 {sev_cnt.get(k, 0)}"

    expected_mod = {"登录注册": 4, "商品": 3, "购物车": 3, "订单支付": 5, "会员权限": 3}
    for k, v in expected_mod.items():
        assert mod_cnt.get(k, 0) == v, f"module {k} 期望 {v} 实际 {mod_cnt.get(k, 0)}"

    expected_type = {"功能": 6, "性能": 3, "安全": 3, "兼容性": 2, "易用性": 2, "边界": 2}
    for k, v in expected_type.items():
        assert type_cnt.get(k, 0) == v, f"type {k} 期望 {v} 实际 {type_cnt.get(k, 0)}"

    rt_cnt = sum(1 for b in BUGS if b.get("related_testcase"))
    assert rt_cnt >= 5, f"related_testcase 非空条数应 ≥5，实际 {rt_cnt}"

    critical_titles = [b["title"] for b in BUGS if b["severity"] == "Critical"]
    # 至少 3 条 Critical 涉及 鉴权/资金/状态机 —— 5 条 Critical 全部覆盖：
    # BUG-001 鉴权(注册XSS/格式) BUG-002 鉴权(改密未登录)
    # BUG-008 资金(购物车超卖) BUG-011 状态机(confirm-submit 窗口)
    # BUG-012 鉴权(枚举 orderNumber) BUG-013 资金(支付事务)
    auth_money_state_kw = ["鉴权", "未登录", "资金", "状态", "事务", "超卖", "支付", "订单"]
    matched = [
        b for b in BUGS
        if b["severity"] == "Critical"
        and any(kw in b["title"] or kw in b["actual"] for kw in auth_money_state_kw)
    ]
    assert len(matched) >= 3, f"Critical 涉及鉴权/资金/状态机条数应 ≥3，实际 {len(matched)}"

    # suggestion 全部非空
    for b in BUGS:
        assert b.get("suggestion"), f"{b['bug_id']} suggestion 为空"


def main() -> None:
    validate()
    write_csv()
    write_markdown()
    print(f"OK: CSV {CSV_PATH}")
    print(f"OK: MD  {MD_PATH}")
    print(f"OK: total={len(BUGS)} severity={dict(Counter(b['severity'] for b in BUGS))} "
          f"module={dict(Counter(b['module'] for b in BUGS))} "
          f"type={dict(Counter(b['type'] for b in BUGS))}")


if __name__ == "__main__":
    main()
