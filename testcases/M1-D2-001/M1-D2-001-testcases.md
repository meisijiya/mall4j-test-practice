# M1-D2-001 测试用例集（离线设计草稿）

> 共 **90** 条用例 · 登录/注册 40 + 商品 30 + 购物车 20

> **设计依据**：CONTEXT.md 模块边界 + 可测点速查 / lessons/0004 用例方法论 / `yami-shop-api` Controller 源码静态分析

> **执行状态**：⏳ 离线草稿，待 D1 环境跑通后回填 actual 结果到 `evidence` 字段

## 用例表

| id | module | scenario | type | priority | method | endpoint | pre_condition | input | expected | remarks |
|---|---|---|---|---|---|---|---|---|---|---|
| LOGIN-001 | 登录-正常账号密码 | scenario | P0 | POST | /sso/login | 已注册账号 test001/123456 | userName=test001&passWord=RSA(123456) | 返回 200 + token + 用户信息 | 正确凭证主链路 |
| LOGIN-002 | 登录-错误密码 | scenario | P0 | POST | /sso/login | 已注册账号 | userName=test001&passWord=RSA(wrongpwd) | 返回 401 用户名或密码错误 | 密码错误分支 |
| LOGIN-003 | 登录-空账号 | boundary | P0 | POST | /sso/login | 无 | userName=&passWord=RSA(123456) | 返回 400 参数校验失败 | 必填校验 |
| LOGIN-004 | 登录-空密码 | boundary | P0 | POST | /sso/login | 无 | userName=test001&passWord= | 返回 400 参数校验失败 | 必填校验 |
| LOGIN-005 | 登录-账号不存在 | scenario | P1 | POST | /sso/login | 无 | userName=ghost_user&passWord=RSA(123456) | 返回 401 用户名或密码错误 | 账号不存在不应暴露注册信息 |
| LOGIN-006 | 登录-账号禁用 status=0 | scenario | P1 | POST | /sso/login | 禁用账号 test002 | userName=test002&passWord=RSA(123456) | 返回 403 账号已被禁用 | 鉴权链-禁用账号 |
| LOGIN-007 | 登录-并发同账号 | scenario | P2 | POST | /sso/login | test001 | 100 并发 /sso/login | 全部成功或最后一次覆盖幂等成功 | 幂等性-不会出现多次颁发不同 token 后业务异常 |
| LOGIN-008 | 登录-Sql 注入尝试 | security | P0 | POST | /sso/login | 无 | userName=' OR 1=1 --&passWord=RSA(x) | 返回 401 而非 200 全表通过 | 鉴权链-SQL 注入 |
| REG-001 | 注册-正常手机号+密码 | scenario | P0 | POST | /user/register | 新手机号未注册 + checkRegisterSmsFlag=valid | {mobile:13900000001, passWord:RSA(123456), userName:test100, checkRegisterSmsFlag:valid} | 返回 200 + tokenInfoVO {accessToken, refreshToken, expiresIn} | 注册主链路 |
| REG-002 | 注册-重复用户名 | scenario | P0 | POST | /user/register | test001 已注册 | {userName:test001, passWord:RSA(123456), mobile:13900000099} | 返回 500 业务异常 '该用户名已注册，无法重新注册' | 唯一性约束 |
| REG-003 | 注册-手机号为空 | boundary | P0 | POST | /user/register | 无 | {mobile:'', passWord:RSA(123456), userName:test101} | 返回 400 参数校验失败 | 必填校验 |
| REG-004 | 注册-密码为空 | boundary | P0 | POST | /user/register | 无 | {mobile:13900000002, passWord:'', userName:test102} | 返回 500 业务异常 '解密后密码为空' | 密码 RSA 解密后空 |
| REG-005 | 注册-验证码标识失效 | scenario | P1 | POST | /user/register | 验证码 5 分钟前过期 | {checkRegisterSmsFlag:expired} | 返回 500 验证码失效 | 业务约束-验证码 |
| REG-006 | 注册-nickName 为空回退 userName | scenario | P1 | POST | /user/register | 无 | {userName:test103, passWord:RSA(123456), nickName:''} | 数据库中 nickName = test103 | 回退逻辑 |
| REG-007 | 注册-邮箱格式非法 | boundary | P1 | POST | /user/register | 无 | {userMail:'not-an-email'} | 返回 400 或数据库字段允许任意字符串 | 邮箱字段弱约束 |
| REG-008 | 注册-手机号格式非法 | boundary | P0 | POST | /user/register | 无 | {mobile:'abc'} | 返回 400 参数校验失败 | 格式校验 |
| REG-009 | 注册-密码长度边界值 | boundary | P1 | POST | /user/register | 无 | passWord=RSA(1) / RSA(1234567890123456) | 1 位与 16 位均通过 | 下限/上限 |
| REG-010 | 注册-重复提交 | scenario | P1 | POST | /user/register | test104 已注册 | 两次提交相同 userName=test104 | 第二次返回 500 用户名已注册 | 幂等性 |
| REG-011 | 注册-XSS 注入尝试 | security | P1 | POST | /user/register | 无 | {userName:'<script>alert(1)</script>'} | 返回 400 或数据库 escape 后存储 | 前端 XSS 防护 |
| REG-012 | 注册-返回 userId 唯一 | scenario | P2 | POST | /user/register | 无 | 连注册两个不同用户 | 两次返回 userId 不同（simpleUUID） | 幂等性-主键生成 |
| UPD-001 | 改密-正常路径 | scenario | P0 | PUT | /user/updatePwd | test001 已登录 + 原密码 123456 | {nickName:test001, passWord:RSA(654321)} | 返回 200，DB 中 loginPassword 已更新 | 主链路 |
| UPD-002 | 改密-新密码与原密码相同 | scenario | P0 | PUT | /user/updatePwd | test001 原密码 123456 | {nickName:test001, passWord:RSA(123456)} | 返回 500 '新密码不能与原密码相同' | 业务约束 |
| UPD-003 | 改密-用户不存在 | scenario | P0 | PUT | /user/updatePwd | 无 | {nickName:ghost, passWord:RSA(123456)} | 返回 500 '无法获取用户信息' | 异常路径 |
| UPD-004 | 改密-密码 RSA 解密失败 | boundary | P1 | PUT | /user/updatePwd | test001 | {nickName:test001, passWord:'not-encrypted'} | 返回 500 '新密码不能为空' | 密码解密失败 |
| UPD-005 | 改密-无登录态 | scenario | P0 | PUT | /user/updatePwd | 未携带 token | {nickName:test001, passWord:RSA(654321)} | 返回 401 未登录 | 鉴权链 |
| UPD-006 | 改密-token 过期 | scenario | P0 | PUT | /user/updatePwd | token 已过期 1 小时 | {nickName:test001, passWord:RSA(654321)} | 返回 401 token 过期 | 鉴权链-过期 token |
| UPD-007 | 查看用户信息 | scenario | P0 | GET | /p/user/userInfo | test001 已登录 | 无 body | 返回 userInfo {userId, nickName, userMail, mobile} | 主链路 |
| UPD-008 | 修改用户信息-正常 | scenario | P1 | PUT | /p/user/setUserInfo | test001 已登录 | {nickName:test001-new, userMail:test001@x.com} | 返回 200，DB 中字段已更新 | 主链路 |
| UPD-009 | 查看用户信息-未登录 | scenario | P0 | GET | /p/user/userInfo | 无 | 无 | 返回 401 未登录 | 鉴权链 |
| UPD-010 | 改密-并发同账号 | scenario | P2 | PUT | /user/updatePwd | test001 | 10 并发 updatePwd | 最终密码 = 其中之一，且不抛乐观锁异常 | 并发安全 |
| SMS-001 | 发送验证码-正常 | scenario | P0 | POST | /p/sms/send | 已登录 + 新手机号 | {mobile:'13900000010'} | 返回 200 + 验证码已发送（Mock 日志） | 主链路 |
| SMS-002 | 发送验证码-手机号非法 | boundary | P0 | POST | /p/sms/send | 已登录 | {mobile:'abc'} | 返回 400 手机号格式错误 | 格式校验 |
| SMS-003 | 发送验证码-未登录 | scenario | P0 | POST | /p/sms/send | 无 | {mobile:'13900000011'} | 返回 401 未登录 | 鉴权链 |
| SMS-004 | 发送验证码-60s 重发限制 | scenario | P1 | POST | /p/sms/send | 已登录 | 60s 内连发 2 次 | 第二次返回 500 发送过于频繁 | 限流 |
| SMS-005 | 注册链路-验证码校验失败 | scenario | P0 | POST | /user/register | 无效 checkRegisterSmsFlag | {mobile:'13900000012', checkRegisterSmsFlag:'fake'} | 返回 500 验证码失效 | 业务约束 |
| SMS-006 | 登录链路-短信验证码登录 | scenario | P1 | POST | /sso/loginByMobile | 已发送验证码 | {mobile:'13900000013', code:'123456'} | 返回 200 + token | 短信登录主链路（如有） |
| SMS-007 | 登录链路-验证码错误 3 次 | scenario | P1 | POST | /sso/loginByMobile | 无 | 连续 3 次错误验证码 | 第 3 次返回 500 验证码错误次数超限 | 防爆破 |
| SMS-008 | 发送验证码-空手机号 | boundary | P0 | POST | /p/sms/send | 已登录 | {mobile:''} | 返回 400 手机号不能为空 | 必填校验 |
| SMS-009 | 发送验证码-日发送上限 | scenario | P2 | POST | /p/sms/send | 已登录 | 同一账号日发送 100 次 | 达到上限返回 500 日发送次数超限 | 限流-日上限 |
| SMS-010 | 发送验证码-异地登录 | security | P1 | POST | /p/sms/send | 已登录 + IP 变化 | 切换 IP 后调用 | 返回 200 但触发风控二次验证（视实现） | 风控 |
| PROD-001 | 商品列表-正常分页 | scenario | P0 | GET | /prod/pageProd | 已上架分类 1 | ?categoryId=1&page=1&size=10 | 返回 IPage<ProductDto> records.length<=10 | 主链路 |
| PROD-002 | 商品列表-page=0 | boundary | P1 | GET | /prod/pageProd | 无 | ?categoryId=1&page=0&size=10 | 返回 400 或默认 page=1 | 分页边界 |
| PROD-003 | 商品列表-page=-1 | boundary | P1 | GET | /prod/pageProd | 无 | ?categoryId=1&page=-1&size=10 | 返回 400 参数错误 | 分页边界 |
| PROD-004 | 商品列表-size=0 | boundary | P1 | GET | /prod/pageProd | 无 | ?categoryId=1&page=1&size=0 | 返回 400 size 必须大于 0 | 分页边界 |
| PROD-005 | 商品列表-size=99999 | boundary | P1 | GET | /prod/pageProd | 无 | ?categoryId=1&page=1&size=99999 | 返回 400 或最大 100 | 分页上限 |
| PROD-006 | 商品列表-总数 0 | boundary | P1 | GET | /prod/pageProd | 空分类 | ?categoryId=999999&page=1&size=10 | 返回 records=[] total=0 | 空结果集 |
| PROD-007 | 商品列表-总数 1 | boundary | P1 | GET | /prod/pageProd | 单商品分类 | ?categoryId=2&page=1&size=10 | 返回 records.length=1 | 边界 |
| PROD-008 | 商品列表-下架商品过滤 | scenario | P1 | GET | /prod/pageProd | 分类含下架商品 | ?categoryId=1 | 下架商品不出现在 records | 业务约束 |
| PROD-009 | 商品详情-正常 | scenario | P0 | GET | /prod/prodInfo | 已上架商品 prodId=10001 | ?prodId=10001 | 返回 ProductDto 含 skuList / img / price | 主链路 |
| PROD-010 | 商品详情-prodId 不存在 | boundary | P0 | GET | /prod/prodInfo | 无 | ?prodId=99999999 | 返回 200 但 data=null 或 500 业务异常 | 异常路径 |
| PROD-011 | 商品详情-prodId=0 | boundary | P1 | GET | /prod/prodInfo | 无 | ?prodId=0 | 返回 400 参数错误 | 边界 |
| PROD-012 | 商品详情-prodId 负数 | boundary | P1 | GET | /prod/prodInfo | 无 | ?prodId=-1 | 返回 400 参数错误 | 边界 |
| PROD-013 | 商品详情-prodId 字符串 | boundary | P1 | GET | /prod/prodInfo | 无 | ?prodId=abc | 返回 400 类型错误 | 类型校验 |
| PROD-014 | 商品详情-SQL 注入 | security | P0 | GET | /prod/prodInfo | 无 | ?prodId=1 OR 1=1 | 返回 400 而非全表 | SQL 注入 |
| PROD-015 | 获取商品全部 SKU | scenario | P0 | GET | /sku/getSkuList | prodId=10001 多 SKU | ?prodId=10001 | 返回 List<SkuDto> 含全部 SKU 组合 | 主链路 |
| PROD-016 | SKU 列表-prodId 不存在 | boundary | P1 | GET | /sku/getSkuList | 无 | ?prodId=99999999 | 返回 [] 或 500 | 异常路径 |
| PROD-017 | 分类信息-顶级分类 | scenario | P0 | GET | /category/categoryInfo | 无 | ?parentId=0 | 返回所有顶级分类 parentId=0 | 主链路 |
| PROD-018 | 分类信息-二级分类 | scenario | P0 | GET | /category/categoryInfo | 无 | ?parentId=1 | 返回 parentId=1 的二级分类 | 主链路 |
| PROD-019 | 分类信息-parentId 负数 | boundary | P1 | GET | /category/categoryInfo | 无 | ?parentId=-1 | 返回 400 或全部 | 边界 |
| PROD-020 | 商品分组标签列表 | scenario | P0 | GET | /prod/tag/prodTagList | 无 | 无 | 返回 List<ProdTagDto> 全部标签 | 主链路 |
| PROD-021 | 通过 tagId 取商品列表 | scenario | P0 | GET | /prod/prodListByTagId | tagId=1 有商品 | ?tagId=1&page=1&size=10 | 返回该标签下商品列表 | 主链路 |
| PROD-022 | 搜索商品-正常关键字 | scenario | P0 | GET | /search/searchProdPage | 已上架含 '手机' 商品 | ?prodName=手机&page=1&size=10 | 返回含 '手机' 的商品列表 | 主链路 |
| PROD-023 | 搜索商品-空关键字 | boundary | P0 | GET | /search/searchProdPage | 无 | ?prodName=&page=1&size=10 | 返回 400 关键字不能为空 | 必填校验 |
| PROD-024 | 搜索商品-超长关键字 256 | boundary | P1 | GET | /search/searchProdPage | 无 | ?prodName=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 返回 400 长度超限 或返回 [] | 边界 |
| PROD-025 | 新品推荐列表 | scenario | P1 | GET | /prod/lastedProdPage | 无 | ?page=1&size=10 | 返回按上架时间倒序的商品列表 | 主链路 |
| PROD-026 | 每日疯抢列表 | scenario | P1 | GET | /prod/moreBuyProdList | 无 | ?page=1&size=10 | 返回按销量排序的商品列表 | 主链路 |
| PROD-027 | 首页所有标签商品 | scenario | P1 | GET | /prod/tagProdList | 无 | 无 | 返回 List<TagProductDto> | 主链路 |
| PROD-028 | 商品评论数据统计 | scenario | P1 | GET | /prodComm/prodCommData | prodId=10001 有评论 | ?prodId=10001 | 返回 ProdCommDataDto 好评率/好评数/中评数/差评数 | 主链路 |
| PROD-029 | 商品评论分页 | scenario | P1 | GET | /prodComm/prodCommPageByProd | prodId=10001 多评论 | ?prodId=10001&page=1&size=10 | 返回 IPage<ProdCommDto> | 主链路 |
| PROD-030 | 商品详情缓存一致性 | scenario | P2 | GET | /prod/prodInfo | admin 修改商品价格 | 缓存 5 分钟内应失效 | 返回最新价格 | 缓存失效 |
| CART-001 | 加购-正常 | scenario | P0 | POST | /p/shopCart/changeItem | test001 已登录 + prodId/skuId/shopId 有效 + count=1 | {basketId:null, prodId:10001, skuId:20001, shopId:1, count:1} | 返回 200，购物车新增 1 条 | 主链路 |
| CART-002 | 加购-count=0 | boundary | P0 | POST | /p/shopCart/changeItem | 已登录 | {prodId:10001, skuId:20001, shopId:1, count:0} | 返回 500 商品个数不能为 0 | 必填 + 业务 |
| CART-003 | 加购-count 负数 | boundary | P0 | POST | /p/shopCart/changeItem | 已登录 + 购物车已有 prodId 10001 count=2 | {prodId:10001, skuId:20001, shopId:1, count:-1} | 购物车该商品 count 变为 1 | 减数逻辑 |
| CART-004 | 加购-count 负数到 0 | boundary | P0 | POST | /p/shopCart/changeItem | 购物车已有 count=1 | {prodId:10001, skuId:20001, shopId:1, count:-1} | 该商品从购物车移除 | 减数到底删除 |
| CART-005 | 加购-prodId 缺失 | boundary | P0 | POST | /p/shopCart/changeItem | 已登录 | {skuId:20001, shopId:1, count:1} | 返回 400 商品ID不能为空 | @NotNull 触发 |
| CART-006 | 加购-未登录 | scenario | P0 | POST | /p/shopCart/changeItem | 无 token | {prodId:10001, skuId:20001, shopId:1, count:1} | 返回 401 未登录 | 鉴权链 |
| CART-007 | 删除单条-正常 | scenario | P0 | DELETE | /p/shopCart/deleteItem | 购物车有 basketId=50001 | {[50001]} | 返回 200，该条移除 | 主链路 |
| CART-008 | 删除单条-basketId 不存在 | boundary | P1 | DELETE | /p/shopCart/deleteItem | 已登录 | {[99999999]} | 返回 200 但无删除（幂等） | 幂等性 |
| CART-009 | 清空购物车-正常 | scenario | P0 | DELETE | /p/shopCart/deleteAll | 购物车有商品 | 无 body | 返回 200，购物车为空 | 主链路 |
| CART-010 | 清空购物车-已是空 | scenario | P1 | DELETE | /p/shopCart/deleteAll | 购物车已空 | 无 body | 返回 200 幂等成功 | 幂等性 |
| CART-011 | 购物车商品数量 | scenario | P0 | GET | /p/shopCart/prodCount | 购物车有 3 条 | 无 | 返回 3 | 主链路 |
| CART-012 | 购物车商品数量-未登录 | scenario | P0 | GET | /p/shopCart/prodCount | 无 token | 无 | 返回 401 未登录 | 鉴权链 |
| CART-013 | 购物车信息-全选 | scenario | P0 | POST | /p/shopCart/info | 购物车 3 条 | {basketId1:{}, basketId2:{}, basketId3:{}} | 返回 3 条 ShopCartDto | 主链路 |
| CART-014 | 购物车信息-空 basketIds | boundary | P1 | POST | /p/shopCart/info | 已登录 | {} | 返回 [] 或购物车全部 | 边界 |
| CART-015 | 失效商品列表 | scenario | P1 | GET | /p/shopCart/expiryProdList | 购物车有失效商品 | 无 | 返回 List<ShopCartExpiryItemDto> | 主链路 |
| CART-016 | 清空失效商品 | scenario | P1 | DELETE | /p/shopCart/cleanExpiryProdList | 购物车有失效商品 | 无 | 返回 200，失效商品清空 | 主链路 |
| CART-017 | 总计-多选 | scenario | P0 | POST | /p/shopCart/totalPay | 已登录 + 选中 3 条 | {[50001, 50002, 50003]} | 返回 ShopCartAmountDto {totalPay, totalCount} | 主链路 |
| CART-018 | 总计-空数组 | boundary | P1 | POST | /p/shopCart/totalPay | 已登录 | {[]} | 返回 totalPay=0 totalCount=0 | 边界 |
| CART-019 | 总计-未登录 | scenario | P0 | POST | /p/shopCart/totalPay | 无 token | {[50001]} | 返回 401 未登录 | 鉴权链 |
| CART-020 | 加购-并发同 SKU 超卖防护 | scenario | P0 | POST | /p/shopCart/changeItem | 商品库存 10 | 100 并发 changeItem count=1 | 最终购物车 count 之和 <= 10 或全部拒绝 | 分布式锁-库存超卖 |

## 统计

- 总数：**90** 条
- 登录/注册：**40** 条
- 商品：**30** 条
- 购物车：**20** 条

### 按类型分布

- P0: 47
- P1: 38
- P2: 5

### 按优先级分布

- DELETE: 5
- GET: 35
- POST: 42
- PUT: 8

## 待回填

- 每个用例执行后：实际输入 / 实际响应 / 通过/失败 / 截图
- 缺陷：缺陷编号 + 重现步骤 + 优先级
- 兼容性：Chrome / Edge / Safari / Firefox × 移动端 H5
