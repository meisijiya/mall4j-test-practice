# 三流合一 + 订单状态机：订单生命周期 + 6 状态迁移

用户已能用一张 9 行状态迁移表 + 三流定义表完整画出订单生命周期（含超时取消、自动确认收货），并能说出每行触发方、代码入口、副作用；这意味着 M1 阶段"业务理解 → 状态机 → 测试件"链路打通，第 3 课可以直接进入模块边界与第一份接口用例。

## 前置基础
- Java + Python 基础语法 / 接口测试基本概念（HTTP / JSON / 状态码）。
- 已学完第 1 课：mall4j 业务定位、三端架构、五流贯通、七大模块、主链路 6 步。

## 本节收获
- 三流 = 同一笔订单的三个观察面（资金 / 信息 / 物流），必须同步前进，孤立单点测试不写进用例库。
- 订单 6 状态枚举：UNPAY=1 / PADYED=2 / CONSIGNMENT=3 / CONFIRM=4 / SUCCESS=5 / CLOSE=6，存储在 `tz_order.status`。
- 9 行核心状态迁移表：提交→1、支付→2、超时 30 分钟/手动取消→6、发货→3、发货前整单退→6、确认收货→4、15 天自动→5、评价→5。
- 资金流三道幂等关：`payNo` 流水号 + 数据库乐观锁（`version+1`）+ 上层订单状态校验；金额源 = `tz_order_settlement.pay_amount`，不信前端传入。
- 信息流关键设计：地址快照写入 `tz_user_addr_order`（不改历史订单）、`ConfirmOrderCache` 提交即清理、`PaySuccessOrderEvent` 事件总线扩展点。
- 物流关键阈值：`OrderTask.cancelOrder`（30 分钟超时）、`OrderTask.confirmOrder`（15 天自动）均为硬编码，未暴露到配置文件（二开要点）。
- 退款原路返回：仅退款（applyType=1）直接走第三方；退款退货（applyType=2）需等用户回寄物流；最终落到 `tz_order_refund.returnMoneySts = 1`。

## 含义（用户能向面试官讲清楚什么）
- "订单状态机怎么转"：能口述 9 行迁移表，每行说出触发方 + 代码入口 + 副作用。
- "三流怎么测"：资金流抓金额源头 + 回调幂等；信息流抓事件总线 + 缓存清理；物流抓发货防重 + 自动确认收货阈值。
- "支付幂等三道关"：`payNo` + DB 乐观锁 + 订单状态校验三重保险，二开需补 `PayNoticeController` 验签 + 幂等。
- "地址快照意义"：下单后用户改地址不影响历史订单，用 `tz_user_addr_order` 对照用户地址簿验证。
- "开源版边界"：没有"退款中"独立状态；退款走 `tz_order_refund` 子表；物流公司对接为占位（手动回填单号）。

**Status**: active

参见：`../lessons/0002-three-flows-and-order-state-machine.html` · `../reference/0002-order-state-cheatsheet.html`