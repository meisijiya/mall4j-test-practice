#!/usr/bin/env python3
"""
M1-D3-001 用例生成器 — 离线用例草稿生成

设计依据：
- CONTEXT.md 模块边界 + 可测点速查（鉴权链 / 幂等性 / 分布式锁 / 参数校验 / 状态机）
- lessons/0002 三流合一 + 订单状态机（UNPAY→PADYED→CONSIGNMENT→CONFIRM→SUCCESS/CLOSE）
- lessons/0004 用例方法论（等价类 + 边界值 + 场景法 + 状态机 + 判定表）
- 源码静态分析：
  * yami-shop-api/.../controller/OrderController.java  (/p/order/confirm, /p/order/submit)
  * yami-shop-api/.../controller/MyOrderController.java  (orderDetail/myOrder/cancel/receipt/delete/orderCount)
  * yami-shop-api/.../controller/PayController.java  (/p/order/pay, /p/order/normalPay)
  * yami-shop-api/.../controller/DeliveryController.java  (/delivery/check)
  * yami-shop-api/.../controller/UserController.java  (/p/user/userInfo, /p/user/setUserInfo)
  * yami-shop-api/.../controller/AddrController.java  (/p/address/list|addAddr|updateAddr|deleteAddr|defaultAddr|addrInfo)
  * yami-shop-bean/.../app/param/OrderParam.java  (@NotNull addrId)
  * yami-shop-bean/.../app/param/SubmitOrderParam.java  (List<OrderShopParam>)
  * yami-shop-bean/.../app/param/PayParam.java  (@NotBlank orderNumbers, @NotNull payType)
  * yami-shop-bean/.../app/param/AddrParam.java  (8 个 @NotNull 字段)
  * yami-shop-bean/.../app/param/OrderRefundParam.java  (orderNumber/applyType/orderItemId/buyerMsg)
  * yami-shop-bean/.../enums/OrderStatus.java  (1 UNPAY, 2 PADYED, 3 CONSIGNMENT, 4 CONFIRM, 5 SUCCESS, 6 CLOSE)
  * yami-shop-sys/.../controller/SysUserController.java  (/sys/user/page|info|password|info/{userId}|save|update|delete)
  * yami-shop-sys/.../controller/SysRoleController.java  (/sys/role/page|list|info/{roleId}|save|update|delete + @PreAuthorize)
  * yami-shop-sys/.../controller/SysMenuController.java  (/sys/menu/nav|table|list|listRootMenu|listChildrenMenu|info/{menuId}|save|update|delete)

用例总览（合计 60 条）：
  模块 A: 订单/支付  25 条
  模块 B: 会员/权限  15 条
  模块 C: 兼容性/异常 20 条

字段（CSV，11 列）：
  id, module, scenario, type, priority, method, endpoint,
  pre_condition, input, expected, remarks

执行：本脚本产物为 .csv / .md；环境跑通后回填实际执行结果到 evidence 字段。
"""
from pathlib import Path

OUT_DIR = Path(__file__).parent
CSV_PATH = OUT_DIR / "M1-D3-001-testcases.csv"
MD_PATH = OUT_DIR / "M1-D3-001-testcases.md"

# ===== 通用字段 =====
HEADER = [
    "id", "module", "scenario", "type", "priority", "method", "endpoint",
    "pre_condition", "input", "expected", "remarks",
]

# 字段说明：
#   id          — 用例唯一编号（ORDER/MEMBER/ADDR/PERM/COMPAT-NNN）
#   module      — 模块名+测试点
#   scenario    — 测试场景描述（一句中文说明测什么）
#   type        — 用例类型：scenario / boundary / equivalence / security / compatibility / concurrency
#   priority    — 优先级：P0 / P1 / P2
#   method      — HTTP 方法：GET / POST / PUT / DELETE / MIXED（兼容性测试用）
#   endpoint    — 接口路径
#   pre_condition — 前置条件
#   input       — 输入（body 或 query）
#   expected    — 预期响应（业务可观察的现象）
#   remarks     — 备注：源码依据 / 可测点速查标签 / 业务约束

# 优先级分配策略：P0=20（核心主链路+核心安全+鉴权链核心），P1=30（业务约束+边界+鉴权延展），P2=10（兼容性/慢响应/罕见场景）

# ===== 模块 A：订单/支付 25 条 =====
ORDER_CASES = []

# A1 主链路（场景法）— 6 条
order_main_cases = [
    (
        "ORDER-001", "订单", "结算生成订单信息", "scenario", "P0", "POST", "/p/order/confirm",
        "test001 已登录 + 购物车有商品 + 已选地址",
        "{addrId:10001, basketIds:[50001,50002]}",
        "返回 200 + ShopCartOrderMergerDto {actualTotal,total,totalCount,shopCartOrders,orderReduce}",
        "主链路-OrderParam.addrId 触发 ConfirmOrderEvent",
    ),
    (
        "ORDER-002", "订单", "提交订单返回支付流水号", "scenario", "P0", "POST", "/p/order/submit",
        "已 confirm 缓存 + test001 已登录",
        "{orderShopParam:[{shopId:1,remarks:'请发顺丰'}]}",
        "返回 200 + OrderNumbersDto {orderNumbers:'O20240101001,O20240101002'} 多个订单号用逗号分隔",
        "主链路-根据店铺拆单",
    ),
    (
        "ORDER-003", "订单", "支付成功 pay", "scenario", "P0", "POST", "/p/order/pay",
        "test001 已登录 + 待付款订单 orderNumber=O20240101001",
        "{orderNumbers:'O20240101001', payType:1}",
        "返回 200 + paySuccess 更新订单 status=2 PADYED",
        "主链路-payType=1 微信 / =2 支付宝",
    ),
    (
        "ORDER-004", "订单", "普通支付 normalPay", "scenario", "P0", "POST", "/p/order/normalPay",
        "test001 已登录 + 待付款订单",
        "{orderNumbers:'O20240101001', payType:2}",
        "返回 200 + Boolean true",
        "主链路-同 pay 接口但返回 Boolean",
    ),
    (
        "ORDER-005", "订单", "确认收货", "scenario", "P0", "PUT", "/p/myOrder/receipt/{orderNumber}",
        "test001 已登录 + 订单 status=3 CONSIGNMENT",
        "PUT /p/myOrder/receipt/O20240101001",
        "返回 200 + status=4 CONFIRM",
        "主链路-CONFIRM 触发商品缓存清除",
    ),
    (
        "ORDER-006", "订单", "查看物流", "scenario", "P1", "GET", "/delivery/check",
        "已发货订单 orderNumber=O20240101001 + dvyId 配置 queryUrl",
        "?orderNumber=O20240101001",
        "返回 200 + DeliveryDto {dvyFlowId,companyName,traces}",
        "主链路-第三方物流接口（HttpUtil.get）",
    ),
]
ORDER_CASES.extend(order_main_cases)

# A2 状态机（场景法）— 8 条
order_state_cases = [
    (
        "ORDER-007", "订单", "状态机-待付款→取消订单", "scenario", "P0", "PUT", "/p/myOrder/cancel/{orderNumber}",
        "test001 已登录 + 订单 status=1 UNPAY",
        "PUT /p/myOrder/cancel/O20240101001",
        "返回 200 + status=6 CLOSE + 库存还原",
        "状态机-UNPAY→CLOSE",
    ),
    (
        "ORDER-008", "订单", "状态机-已付款订单不可取消", "scenario", "P0", "PUT", "/p/myOrder/cancel/{orderNumber}",
        "test001 已登录 + 订单 status=2 PADYED",
        "PUT /p/myOrder/cancel/O20240101002",
        "返回 500 '订单已支付，无法取消订单'",
        "状态机-PADYED 不允许取消",
    ),
    (
        "ORDER-009", "订单", "状态机-商家发货 PADYED→CONSIGNMENT", "scenario", "P0", "POST", "/admin/order/delivery",
        "test001 已登录 + 商家后台 + 订单 status=2 + 已填 dvyId/dvyFlowId",
        "{orderNumber:O20240101002, dvyId:1, dvyFlowId:'SF1234567890'}",
        "返回 200 + status=3 CONSIGNMENT",
        "状态机-PADYED→CONSIGNMENT",
    ),
    (
        "ORDER-010", "订单", "状态机-用户确认收货", "scenario", "P1", "PUT", "/p/myOrder/receipt/{orderNumber}",
        "test001 已登录 + 订单 status=3",
        "PUT /p/myOrder/receipt/O20240101002",
        "返回 200 + status=4 CONFIRM",
        "状态机-CONSIGNMENT→CONFIRM",
    ),
    (
        "ORDER-011", "订单", "状态机-用户评价 CONFIRM→SUCCESS", "scenario", "P1", "POST", "/prodComm",
        "test001 已登录 + 订单 status=4 + 待评论 orderItem",
        "{orderItemId:60001, prodId:10001, content:'好评', score:5}",
        "返回 200 + 订单 status=5 SUCCESS + 商品购买数+1",
        "状态机-CONFIRM→SUCCESS",
    ),
    (
        "ORDER-012", "订单", "查询订单列表 status=0 全部", "scenario", "P1", "GET", "/p/myOrder/myOrder",
        "test001 已登录 + 多笔订单混合状态",
        "?status=0&page=1&size=10",
        "返回全部订单（不限状态）",
        "状态机-按状态查询",
    ),
    (
        "ORDER-013", "订单", "查询订单列表 status=1 待付款", "scenario", "P1", "GET", "/p/myOrder/myOrder",
        "test001 有 3 笔 UNPAY + 2 笔 PADYED",
        "?status=1&page=1&size=10",
        "仅返回 3 笔 status=1 订单",
        "状态机-按状态过滤",
    ),
    (
        "ORDER-014", "订单", "订单数量统计 orderCount", "scenario", "P0", "GET", "/p/myOrder/orderCount",
        "test001 有不同状态订单",
        "无 body",
        "返回 OrderCountData {unPay:3, padyed:2, consignment:1, confirm:1}",
        "状态机-订单数量看板",
    ),
]
ORDER_CASES.extend(order_state_cases)

# A3 幂等性 / 并发 / 鉴权 — 8 条
order_idempotent_cases = [
    (
        "ORDER-015", "订单", "幂等-重复 submit 同一 confirm 缓存", "scenario", "P1", "POST", "/p/order/submit",
        "test001 已 confirm 一次",
        "两次相同 SubmitOrderParam 提交",
        "第二次返回 200 但应提示 '订单已过期，请重新下单' 或新合并订单",
        "幂等性-confirmOrderCache（CONTEXT §3 幂等性）",
    ),
    (
        "ORDER-016", "订单", "幂等-重复 pay 同一订单号", "scenario", "P1", "POST", "/p/order/pay",
        "test001 + orderNumber=O20240101001 已支付",
        "两次相同 PayParam",
        "第二次返回 200 但 paySuccess 应幂等（订单 status 不应回到 UNPAY）",
        "幂等性-支付回调幂等（CONTEXT §3 幂等性）",
    ),
    (
        "ORDER-017", "订单", "幂等-重复 cancel 同一订单", "scenario", "P1", "PUT", "/p/myOrder/cancel/{orderNumber}",
        "订单已 CLOSE",
        "PUT /p/myOrder/cancel/O20240101001",
        "返回 500 '订单已支付，无法取消订单'（业务异常）",
        "幂等性-状态守卫（CONTEXT §3 幂等性）",
    ),
    (
        "ORDER-018", "订单", "并发-同账号并发提交订单", "concurrency", "P1", "POST", "/p/order/submit",
        "test001 已登录 + 库存 10",
        "100 并发 submit 同一 confirm 缓存",
        "应通过 Redisson 分布式锁保证库存不超卖，最终仅 1 个订单号",
        "分布式锁-秒杀场景（CONTEXT §3 分布式锁）",
    ),
    (
        "ORDER-019", "订单", "并发-库存超卖防护", "concurrency", "P1", "POST", "/p/order/submit",
        "SKU 库存 = 1 + 100 并发",
        "100 并发 submit",
        "第 1 个请求成功，其余返回 500 库存不足",
        "分布式锁-Redisson（CONTEXT §3 分布式锁）",
    ),
    (
        "ORDER-020", "订单", "鉴权-未登录访问订单接口", "scenario", "P0", "POST", "/p/order/confirm",
        "无 token",
        "{addrId:10001, basketIds:[50001]}",
        "返回 401 未登录",
        "鉴权链-Sa-Token（CONTEXT §3 鉴权链）",
    ),
    (
        "ORDER-021", "订单", "鉴权-普通用户查他人订单", "scenario", "P1", "GET", "/p/myOrder/orderDetail",
        "test001 已登录 + 订单 O9999 属 test002",
        "?orderNumber=O9999",
        "返回 500 '你没有权限获取该订单信息'",
        "鉴权链-订单归属校验（CONTEXT §3 鉴权链）",
    ),
    (
        "ORDER-022", "订单", "鉴权-token 过期访问订单", "scenario", "P1", "GET", "/p/myOrder/myOrder",
        "test001 token 已过期 1 小时",
        "?status=0",
        "返回 401 token 过期",
        "鉴权链-过期 token（CONTEXT §3 鉴权链）",
    ),
]
ORDER_CASES.extend(order_idempotent_cases)

# A4 参数校验（边界值 / 安全）— 3 条
order_param_cases = [
    (
        "ORDER-023", "订单", "参数-addrId 缺失", "boundary", "P2", "POST", "/p/order/confirm",
        "test001 已登录",
        "{basketIds:[50001]}",
        "返回 400 '地址不能为空'（OrderParam.addrId @NotNull 触发）",
        "参数校验-必填字段（CONTEXT §3 参数校验）",
    ),
    (
        "ORDER-024", "订单", "参数-orderNumbers 缺失", "boundary", "P1", "POST", "/p/order/pay",
        "test001 已登录",
        "{payType:1}",
        "返回 400 '订单号不能为空'（PayParam.orderNumbers @NotBlank 触发）",
        "参数校验-PayParam（CONTEXT §3 参数校验）",
    ),
    (
        "ORDER-025", "订单", "参数-orderNumber SQL 注入", "security", "P1", "POST", "/p/order/pay",
        "test001 已登录",
        "{orderNumbers:'1 OR 1=1 --', payType:1}",
        "返回 400 而非全表匹配",
        "SQL 注入-OrderService.getOrderByOrderNumber（CONTEXT §3 安全）",
    ),
]
ORDER_CASES.extend(order_param_cases)

# ===== 模块 B：会员/权限 15 条 =====
MEMBER_CASES = []

# B1 用户信息 — 5 条
user_info_cases = [
    (
        "MEMBER-001", "会员", "查看用户信息", "scenario", "P0", "GET", "/p/user/userInfo",
        "test001 已登录",
        "无 body",
        "返回 UserDto {userId,nickName,userMail,mobile,pic,status}",
        "主链路",
    ),
    (
        "MEMBER-002", "会员", "修改用户信息", "scenario", "P0", "PUT", "/p/user/setUserInfo",
        "test001 已登录",
        "{nickName:'test001-new', avatarUrl:'https://oss.x.com/a.jpg'}",
        "返回 200 + DB 中 nickName + pic 已更新",
        "主链路",
    ),
    (
        "MEMBER-003", "会员", "nickName 长度边界值", "boundary", "P2", "PUT", "/p/user/setUserInfo",
        "test001 已登录",
        "{nickName:''} / {nickName:'x'*256}",
        "空串应通过（DB 允许），256 字符应通过（UserInfoParam 无 @Size 约束）",
        "边界值-弱约束",
    ),
    (
        "MEMBER-004", "会员", "头像 URL XSS 注入", "security", "P1", "PUT", "/p/user/setUserInfo",
        "test001 已登录",
        "{avatarUrl:'javascript:alert(1)'}",
        "返回 200 但前端展示时不应执行脚本（依赖前端过滤）",
        "XSS-UserInfoParam 字段弱约束（CONTEXT §3 安全）",
    ),
    (
        "MEMBER-005", "会员", "查看用户信息未登录", "scenario", "P1", "GET", "/p/user/userInfo",
        "无 token",
        "无 body",
        "返回 401 未登录",
        "鉴权链（CONTEXT §3 鉴权链）",
    ),
]
MEMBER_CASES.extend(user_info_cases)

# B2 地址管理 — 8 条
addr_cases = [
    (
        "ADDR-001", "会员", "地址列表", "scenario", "P0", "GET", "/p/address/list",
        "test001 已登录 + 已有 2 个地址",
        "无 body",
        "返回 List<UserAddrDto> 按 commonAddr DESC, updateTime DESC 排序",
        "主链路",
    ),
    (
        "ADDR-002", "会员", "新增地址", "scenario", "P0", "POST", "/p/address/addAddr",
        "test001 已登录 + 已有 1 个默认地址",
        "{addrId:0, receiver:'张三', mobile:'13900000001', addr:'中山路 1 号', provinceId:1, cityId:2, areaId:3, province:'广东', city:'广州', area:'天河', postCode:'510000'}",
        "返回 200 '添加地址成功' + DB 新增 + commonAddr=0（首条地址自动=1）",
        "主链路",
    ),
    (
        "ADDR-003", "会员", "新增首条地址自动设为默认", "scenario", "P1", "POST", "/p/address/addAddr",
        "test001 已登录 + 当前无地址",
        "{addrId:0, receiver:'张三', ...}",
        "返回 200 + 新增地址 commonAddr=1",
        "业务约束-AddrController.addAddr(addrCount==0)",
    ),
    (
        "ADDR-004", "会员", "修改地址", "scenario", "P1", "PUT", "/p/address/updateAddr",
        "test001 已登录 + addrId=10001 存在",
        "{addrId:10001, receiver:'李四', ...}",
        "返回 200 '修改地址成功' + DB 已更新",
        "主链路",
    ),
    (
        "ADDR-005", "会员", "删除默认地址被拒", "scenario", "P1", "DELETE", "/p/address/deleteAddr/{addrId}",
        "test001 + addrId=10001 commonAddr=1",
        "DELETE /p/address/deleteAddr/10001",
        "返回 500 '默认地址无法删除'",
        "业务约束-AddrController.deleteDvy",
    ),
    (
        "ADDR-006", "会员", "删除非默认地址", "scenario", "P1", "DELETE", "/p/address/deleteAddr/{addrId}",
        "test001 + addrId=10002 commonAddr=0",
        "DELETE /p/address/deleteAddr/10002",
        "返回 200 '删除地址成功'",
        "主链路",
    ),
    (
        "ADDR-007", "会员", "设置默认地址", "scenario", "P0", "PUT", "/p/address/defaultAddr/{addrId}",
        "test001 + addrId=10002 当前非默认",
        "PUT /p/address/defaultAddr/10002",
        "返回 200 + DB 中 10002 commonAddr=1 + 10001 commonAddr=0",
        "主链路",
    ),
    (
        "ADDR-008", "会员", "参数校验 receiver 缺失", "boundary", "P2", "POST", "/p/address/addAddr",
        "test001 已登录",
        "{addrId:0, mobile:'13900000001', addr:'x', provinceId:1, cityId:2, areaId:3, province:'x', city:'x', area:'x'}",
        "返回 400 '收货人不能为空'",
        "参数校验-@NotNull receiver（CONTEXT §3 参数校验）",
    ),
]
MEMBER_CASES.extend(addr_cases)

# B3 后台权限 — 2 条
sys_perm_cases = [
    (
        "PERM-001", "权限", "前台用户访问 admin 接口被拒", "scenario", "P1", "GET", "/sys/user/page",
        "前台 test001 token（无 sysUser 权限）",
        "?page=1&size=10",
        "返回 403 无权限",
        "鉴权链-Spring Security @PreAuthorize（CONTEXT §3 鉴权链）",
    ),
    (
        "PERM-002", "权限", "超管访问 sys/role/list", "scenario", "P2", "GET", "/sys/role/list",
        "超管已登录",
        "无 body",
        "返回 200 + List<SysRole>",
        "主链路-@PreAuthorize('sys:role:list')",
    ),
]
MEMBER_CASES.extend(sys_perm_cases)

# ===== 模块 C：兼容性/异常 20 条 =====
COMPAT_CASES = []

# C1 浏览器/移动端兼容 — 6 条
compat_browser_cases = [
    (
        "COMPAT-001", "兼容性", "Chrome 最新版 PC 端", "compatibility", "P0", "MIXED", "MIXED",
        "Chrome ≥ 120 + Win11",
        "完整下单流程（登录→商品→加购→结算→支付→收货）",
        "所有页面渲染正常，接口 200，无 console error",
        "兼容性-PC Chrome",
    ),
    (
        "COMPAT-002", "兼容性", "Edge 最新版 PC 端", "compatibility", "P2", "MIXED", "MIXED",
        "Edge ≥ 120 + Win11",
        "同上完整流程",
        "所有页面渲染正常",
        "兼容性-PC Edge",
    ),
    (
        "COMPAT-003", "兼容性", "Firefox 最新版 PC 端", "compatibility", "P1", "MIXED", "MIXED",
        "Firefox ≥ 121 + Win11",
        "同上完整流程",
        "所有页面渲染正常（注意 SVG/CSS 兼容）",
        "兼容性-PC Firefox",
    ),
    (
        "COMPAT-004", "兼容性", "Safari 最新版 Mac 端", "compatibility", "P1", "MIXED", "MIXED",
        "Safari ≥ 17 + macOS Sonoma",
        "同上完整流程",
        "所有页面渲染正常（注意日期/支付组件兼容）",
        "兼容性-PC Safari",
    ),
    (
        "COMPAT-005", "兼容性", "iOS Safari H5", "compatibility", "P2", "MIXED", "MIXED",
        "iOS 17 Safari",
        "完整下单流程",
        "H5 页面渲染 + 微信支付跳转正常",
        "兼容性-移动端 Safari",
    ),
    (
        "COMPAT-006", "兼容性", "Android Chrome H5", "compatibility", "P2", "MIXED", "MIXED",
        "Android 14 Chrome",
        "完整下单流程",
        "H5 页面渲染 + 支付宝跳转正常",
        "兼容性-移动端 Chrome",
    ),
]
COMPAT_CASES.extend(compat_browser_cases)

# C2 网络异常 — 3 条
compat_network_cases = [
    (
        "COMPAT-007", "兼容性", "弱网 3G", "compatibility", "P2", "POST", "/p/order/submit",
        "Chrome DevTools throttle 3G + test001 已登录",
        "{orderShopParam:[{shopId:1}]}",
        "提交按钮 loading 状态保持，最终成功或超时提示",
        "兼容性-弱网",
    ),
    (
        "COMPAT-008", "兼容性", "断网重连", "compatibility", "P2", "POST", "/p/order/submit",
        "提交过程中关闭 Wi-Fi 后恢复",
        "{orderShopParam:[{shopId:1}]}",
        "前端应捕获网络异常并允许重试",
        "兼容性-断网",
    ),
    (
        "COMPAT-009", "兼容性", "慢响应 5s+", "compatibility", "P2", "GET", "/p/myOrder/myOrder",
        "DevTools throttle 5000ms latency",
        "?status=0",
        "页面显示 loading 不应白屏，超时后友好提示",
        "兼容性-慢响应",
    ),
]
COMPAT_CASES.extend(compat_network_cases)

# C3 异常输入 — 4 条
compat_input_cases = [
    (
        "COMPAT-010", "兼容性", "超长字符串 10000 字符", "boundary", "P2", "PUT", "/p/user/setUserInfo",
        "test001 已登录",
        "{nickName:'x'*10000, avatarUrl:'https://oss.x.com/a.jpg'}",
        "返回 200 或 400（依赖 DB 字段长度）",
        "边界值-超长输入",
    ),
    (
        "COMPAT-011", "兼容性", "特殊字符 emoji", "boundary", "P2", "PUT", "/p/user/setUserInfo",
        "test001 已登录",
        "{nickName:'用户😀🎉'}",
        "返回 200 + DB 正确存储（utf8mb4）",
        "边界值-emoji",
    ),
    (
        "COMPAT-012", "兼容性", "SQL 注入尝试", "security", "P0", "POST", "/p/address/addAddr",
        "test001 已登录",
        "{addrId:0, receiver:\"' OR 1=1 --\", mobile:'13900000001', provinceId:1, cityId:2, areaId:3, province:'x', city:'x', area:'x'}",
        "返回 400 而非全表泄露",
        "SQL 注入-AddrParam 字段（CONTEXT §3 安全）",
    ),
    (
        "COMPAT-013", "兼容性", "XSS 注入尝试", "security", "P0", "PUT", "/p/user/setUserInfo",
        "test001 已登录",
        "{nickName:'<script>alert(1)</script>', avatarUrl:''}",
        "返回 200 但 DB escape 后存储，前端展示安全",
        "XSS-UserInfoParam.nickName（CONTEXT §3 安全）",
    ),
]
COMPAT_CASES.extend(compat_input_cases)

# C4 边界值 — 4 条
compat_boundary_cases = [
    (
        "COMPAT-014", "兼容性", "金额 0.01 元", "boundary", "P1", "POST", "/p/order/pay",
        "订单金额 = 0.01",
        "{orderNumbers:'O_MIN', payType:1}",
        "返回 200 + 支付成功（最小金额）",
        "边界值-最小金额",
    ),
    (
        "COMPAT-015", "兼容性", "金额 999999.99 元", "boundary", "P1", "POST", "/p/order/pay",
        "订单金额 = 999999.99",
        "{orderNumbers:'O_MAX', payType:1}",
        "返回 200 + 支付成功（大额）",
        "边界值-大额",
    ),
    (
        "COMPAT-016", "兼容性", "金额负数", "boundary", "P0", "POST", "/p/order/pay",
        "订单金额 = -100",
        "{orderNumbers:'O_NEG', payType:1}",
        "返回 500 业务异常（订单金额不能为负）",
        "边界值-负数",
    ),
    (
        "COMPAT-017", "兼容性", "金额 0 元", "boundary", "P0", "POST", "/p/order/pay",
        "订单金额 = 0",
        "{orderNumbers:'O_ZERO', payType:1}",
        "返回 500 业务异常（订单金额不能为 0）",
        "边界值-0",
    ),
]
COMPAT_CASES.extend(compat_boundary_cases)

# C5 国际化/编码 — 3 条
compat_i18n_cases = [
    (
        "COMPAT-018", "兼容性", "中文昵称/地址", "compatibility", "P2", "POST", "/p/address/addAddr",
        "test001 已登录",
        "{addrId:0, receiver:'张三', addr:'广州市天河区中山大道 123 号', provinceId:1, cityId:2, areaId:3, province:'广东省', city:'广州市', area:'天河区', mobile:'13900000001', postCode:'510000'}",
        "返回 200 + DB 正确存储 utf8mb4",
        "国际化-中文",
    ),
    (
        "COMPAT-019", "兼容性", "英文昵称/地址", "compatibility", "P2", "POST", "/p/address/addAddr",
        "test001 已登录",
        "{addrId:0, receiver:'John Smith', addr:'123 Main Street, Apt 4B', provinceId:1, cityId:2, areaId:3, province:'CA', city:'LA', area:'Downtown', mobile:'13900000001', postCode:'90001'}",
        "返回 200 + DB 正确存储",
        "国际化-英文",
    ),
    (
        "COMPAT-020", "兼容性", "中英数字混排 + URL 编码", "compatibility", "P2", "POST", "/p/address/addAddr",
        "test001 已登录",
        "{addrId:0, receiver:'张三 John 100', addr:'%E5%B9%BF%E5%B7%9E 100 号', provinceId:1, cityId:2, areaId:3, province:'广东省', city:'广州市', area:'天河区', mobile:'13900000001', postCode:'510000'}",
        "返回 200 + 后端正确解码 URL 编码字段",
        "国际化-混排+URL 编码",
    ),
]
COMPAT_CASES.extend(compat_i18n_cases)

# ===== 合并 + 写出 =====
ALL_CASES = ORDER_CASES + MEMBER_CASES + COMPAT_CASES


def to_csv_row(row):
    return ",".join(['"{}"'.format(str(c).replace('"', '""')) for c in row])


def md_table(rows):
    out = ["| " + " | ".join(HEADER) + " |",
           "|" + "|".join(["---"] * len(HEADER)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("\n", " ").replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


with CSV_PATH.open("w", encoding="utf-8") as f:
    f.write(",".join(HEADER) + "\n")
    for row in ALL_CASES:
        f.write(to_csv_row(row) + "\n")

with MD_PATH.open("w", encoding="utf-8") as f:
    f.write("# M1-D3-001 测试用例集（离线设计草稿）\n\n")
    f.write(f"> 共 **{len(ALL_CASES)}** 条用例 · 订单/支付 {len(ORDER_CASES)} + 会员/权限 {len(MEMBER_CASES)} + 兼容性/异常 {len(COMPAT_CASES)}\n\n")
    f.write("> **设计依据**：CONTEXT.md 模块边界 + 可测点速查 / lessons/0002 三流合一+状态机 / lessons/0004 用例方法论 / `yami-shop-api` + `yami-shop-sys` Controller 源码静态分析\n\n")
    f.write("> **执行状态**：⏳ 离线草稿，待 D1 环境跑通后回填 actual 结果到 evidence 字段\n\n")
    f.write("## 用例表\n\n")
    f.write(md_table(ALL_CASES))
    f.write("\n\n## 统计\n\n")
    f.write(f"- 总数：**{len(ALL_CASES)}** 条\n")
    f.write(f"- 订单/支付：**{len(ORDER_CASES)}** 条\n")
    f.write(f"- 会员/权限：**{len(MEMBER_CASES)}** 条\n")
    f.write(f"- 兼容性/异常：**{len(COMPAT_CASES)}** 条\n")
    # 按类型分布
    type_counter = {}
    pri_counter = {}
    method_counter = {}
    for r in ALL_CASES:
        type_counter[r[3]] = type_counter.get(r[3], 0) + 1
        pri_counter[r[4]] = pri_counter.get(r[4], 0) + 1
        method_counter[r[5]] = method_counter.get(r[5], 0) + 1
    f.write("\n### 按类型分布\n\n")
    for k, v in sorted(type_counter.items()):
        f.write(f"- {k}: {v}\n")
    f.write("\n### 按优先级分布\n\n")
    for k, v in sorted(pri_counter.items()):
        f.write(f"- {k}: {v}\n")
    f.write("\n### 按 HTTP method 分布\n\n")
    for k, v in sorted(method_counter.items()):
        f.write(f"- {k}: {v}\n")
    f.write("\n### 与 CONTEXT.md 第 3 节「可测点速查」映射\n\n")
    f.write("- 幂等性（订单/支付/退款）：ORDER-015 / ORDER-016 / ORDER-017\n")
    f.write("- 分布式锁（库存超卖）：ORDER-018 / ORDER-019\n")
    f.write("- 鉴权链（401/403/token 过期）：ORDER-020 / ORDER-021 / ORDER-022 / MEMBER-005 / PERM-001\n")
    f.write("- 参数校验（@NotNull/@NotBlank）：ORDER-023 / ORDER-024 / ADDR-008\n")
    f.write("- SQL 注入 / XSS 防护：ORDER-025 / MEMBER-004 / COMPAT-012 / COMPAT-013\n")
    f.write("\n## 待回填\n\n")
    f.write("- 每个用例执行后：实际输入 / 实际响应 / 通过/失败 / 截图\n")
    f.write("- 缺陷：缺陷编号 + 重现步骤 + 优先级（与 M1-D3 缺陷 18 个对应）\n")
    f.write("- 兼容性：Chrome / Edge / Safari / Firefox × 移动端 H5 实测结果\n")

print(f"OK: {len(ALL_CASES)} cases -> {CSV_PATH.name} + {MD_PATH.name}")
print(f"  A 订单/支付 {len(ORDER_CASES)} / B 会员/权限 {len(MEMBER_CASES)} / C 兼容性/异常 {len(COMPAT_CASES)}")
