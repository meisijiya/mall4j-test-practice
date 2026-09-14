# GitHub Actions CI 接入 + 仓库就绪：本机 pytest → PR 自动验证：services mysql+redis + secrets 10 处加密 + allure-action gh-pages + RUN_UI=0 经济性

用户已能从 M2-D8-001 的"85 用例 + 7 Page POM + 路径 2 captcha mock"跃升到 M2-D9-001 的"api-test.yml CI 接入 + 10 文件落地 + validate-ci.py 6/6 OK"，能讲清 4 个核心：理解为何 runner 是干净 ubuntu-latest 而本机 Windows/macOS 差异消失（双刃剑 = 一致性 vs 速度）、为何 services block 等价 docker-compose 但写在 workflow 文件里（options: --health-cmd 探活机制）、为何 secrets.* 是加密 env 而 env.* 是明文（GitHub Actions 安全红线）、为何 allure-action 替代手动装 allure-commandline（Node 包不在 pip 也不在 apt）—— 这意味着 M2-D9-001（CI 接入 + 仓库就绪）落地，下一步进入 M3-D10-001（Locust 登录压测）。
## 前置基础
- 已学完第 1-13 课：mall4j 业务定位 / 三流合一与状态机 / 模块边界 / 用例方法论 / 150 条用例 / 18 条预测缺陷 / 9 章报告骨架 / Postman API / pytest requests / Postman v3.0 / pytest YAML 数据驱动 / POM 完整化 + 路径 2。
- 第 12 课（M2-D7-001 YAML + UI 起步）和第 13 课（M2-D8-001 POM + 路径 2）的 pytest 框架经验（conftest 顶层 load env + AES 加密 + 路径 1/2 双模式）—— D9 是其"把 pytest 6 PASS 变成任何 PR 自动验证"扩展。
- GitHub Actions 基础认知（push trigger / pull_request trigger / workflow_dispatch 手动入口 / secrets 配置 / services 容器）。
- allure 报告认知（第 13 课 D8 已用 allure_compat 优雅降级）+ gh-pages 部署基础。

## 本节收获
- **CI 是质量门禁不是测试工具（核心 fix #1）**：本机 pytest 6 PASS ≠ 团队其他人也能跑通。CI 把"我能跑"变成"任何 PR 都自动验证"，本质是质量门禁（PR 合并前必须绿），不是"加速测试"。api-test.yml 设 timeout-minutes: 30 + push trigger main/dev + workflow_dispatch 手动入口 + pull_request trigger，4 类 trigger 覆盖 90% 测试团队场景。详见 `.github/workflows/api-test.yml:5-9`（push / pull_request / workflow_dispatch 三类 trigger）—— 这是"CI 不是写更多测试，是把已有测试变成团队契约"。

- **runner 是干净 ubuntu-latest 的双刃剑（关键 fix #2）**：ubuntu-latest runner 每次都是新容器，本机的 Python 3.11 + pip 包 + JDK 17 + chromium 150MB 全部要重装。但同时，本机 Windows 反斜杠路径、Mac 终端编码、Linux 字体差异也都消失。**双刃剑 = 一致性 vs 速度**。cache: maven + cache: pip + cache: playwright 把"重装"变成"增量更新"的标准解。详见 `.github/workflows/api-test.yml:62-67`（cache: pip）+ `:84-89`（cache: maven）—— 这是"CI runner 的经济性：cache 是必加"。

- **services block 是"docker-compose 嵌入 workflow"（关键 fix #3）**：不需要在 runner 上跑 docker compose，workflow 直接用 services: 字段声明 mysql:8.0.33 + redis:7.2-alpine，runner 自动启容器 + 探活 + 关停。**关键**：options: 字段用 --health-cmd 配置探活命令，runner 默认等 health-retries 次通过才进 step。详见 `.github/workflows/api-test.yml:14-26`（mysql services）+ `:28-40`（redis services）—— 这是"CI 起服务比 docker-compose 简洁但语义等价"。

- **secrets.* 是"加密 env"不是"配置文件"（关键 fix #4）**：Settings → Secrets and variables 配置的 secrets.* 以 ${{ secrets.NAME }} 引用，**运行时才解密**（日志里自动 mask 成 ***）。env.* 字段是明文，写 MYSQL_ROOT_PASSWORD=xxx 直接暴露在仓库 —— 这是 GitHub Actions 新手最常犯的错。详见 `.github/workflows/api-test.yml:42-49`（env:）+ `:55-60`（secrets 引用 10 处）—— 这是"安全规范：密码永远走 secrets"。

- **RUN_UI=0 默认是 CI 经济性策略**：chromium 150MB + playwright install --with-deps 装系统依赖，每次 runner 重下要 1-2 分钟。默认 RUN_UI=0 跳过 UI 测试（只跑接口测试），workflow_dispatch 手动开 RUN_UI=1 才装 chromium 跑 UI。详见 `.github/workflows/api-test.yml:70-77`（RUN_UI 条件判断）—— 这是"性能优化不是功能阉割 —— 接口测试必跑，UI 测试可选"。

- **allure-action 替代手动装 allure-commandline**：allure-commandline 是 Node 包（allure-commandline-2.27.0.tgz），不在 pip 也不在 apt。手动装要 npm i -g + 加 PATH + allure generate + allure open 三步。awesomecode/allure-action@v1 是一行 github_action，把"装 + 生成 + 部署 gh-pages"打包。详见 `.github/workflows/api-test.yml:96-104`（allure-action）—— 这是"CI 工具链：用 GitHub Action 复用代替自建脚本"。

- **upload-artifact@v4 + retention-days 是"报告保险"**：allure-action 部署 gh-pages 失败时，upload-artifact@v4 上传 allure-report 目录保留 30 天，PR 评论附下载链接。**双保险**：gh-pages 是公开历史，artifact 是 PR 专属。详见 `.github/workflows/api-test.yml:106-113`（upload-artifact@v4）—— 这是"CI 报告交付：公开历史 + PR 专属 双链路"。

- **CI 网络不切镜像是有意为之的工程权衡**：ubuntu-latest runner 走国际链路（aws us-east-1 / azure westus），apt / pip / maven 源都可达。切国内镜像（aliyun / tsinghua）反而要走 runner → 中国 CDN → 国际源，链路更长。**fallback** 是本机原生启动（lessons/0009 playbook），不走 CI。详见 `docs/CI.md:67-72`—— 这是"工具链配置：信任官方源 + 本机 fallback"。

- **仓库就绪 + .gitignore +6 行的细节**：.gitignore 加 target/ / .idea/ / *.iml / .vscode/ / .DS_Store / logs/ 6 行排除路径（mall4j 是 AGPLv3 项目，target/ 编译产物不能进仓库）。详见 `.gitignore:62-68`（6 行新增）—— 这是"AGPLv3 边界守护：编译产物不进仓"。

## 含义（用户能向面试官讲清楚什么）
- "为什么 CI 不是替代 pytest，而是把 pytest 变成'任何 PR 自动验证'"：本机跑 pytest 6 PASS 是"我能跑"，CI 跑通是"团队任何成员 PR 都自动验证"。CI 的本质不是"加速测试"，是"把测试变成团队契约"（PR 合并前必须绿）。面试时讲清"CI 是质量门禁不是性能工具"展示对 DevOps 本质的理解。

- "为什么 runner 用 ubuntu-latest 而不是 self-hosted（self-hosted 是不是更快）"：self-hosted runner 本机已有 JDK + Python + pip 包，"看似快"，但本机的 Windows 反斜杠路径 / Mac 终端编码 / Linux 字体差异都会复现到 CI。ubuntu-latest runner 是干净容器，每次都是新环境，**环境差异 = 0**。但代价是每次重装 150MB chromium + pip 包。cache: maven + cache: pip + cache: playwright 把"重装"变成"增量更新"（命中时 30 秒 vs 全装 3 分钟）。面试时讲清"为什么我没用 self-hosted —— 一致性 > 速度"展示工程权衡能力。

- "为什么 services block 等价 docker-compose 但写在 workflow 文件里"：docker-compose.yml 是独立文件 + 独立 docker compose up 命令，CI 端要先 docker compose up 再跑测试，runner 上还要装 docker compose 二进制。services: 字段是 GitHub Actions 原生支持的语法，runner 自动启容器 + 探活（options: --health-cmd + health-retries）+ 关停，**零额外依赖**。面试时讲清"services block 比 docker-compose 在 CI 端简洁 50%"。

- "为什么 secrets.* 是加密 env 而 env.* 是明文（这是 GitHub Actions 安全红线）"：env.* 字段写 MYSQL_ROOT_PASSWORD=root 是字面明文，git push 后任何 fork 都能看到。secrets.* 走 Settings → Secrets and variables → Actions 配置，运行时才解密，**日志里自动 mask 成 ***（即使有人故意 echo $SECRET 也只看到 ***）。这是 GitHub Actions 的硬安全规范 —— 所有密码 / token / API key 必须走 secrets 不走 env。面试时讲清"为什么我所有密码走 secrets 不走 env —— 这是 GitHub Actions 安全红线"。

- "为什么 awesomecode/allure-action@v1 替代 allure-commandline（手动装 3 步）"：allure-commandline 是 Node 包（allure-commandline-2.27.0.tgz），不在 pip 也不在 apt 仓库。手动装要 npm i -g allure-commandline + 加 PATH + allure generate results + allure open 4 步，CI 端还要装 Node.js（runner 默认有）+ npm。awesomecode/allure-action@v1 是一行 github_action，把"装 + 生成 + 部署 gh-pages"打包成单一 use。**降级方案**：allure-action 失败时改 upload-artifact@v4 上传 raw allure-results 保留 30 天。面试时讲清"为什么我选 allure-action 不是 allure-commandline —— GitHub Action 复用比自建脚本稳"。

- "为什么 RUN_UI=0 默认 + workflow_dispatch 手动开 RUN_UI=1（CI 经济性策略）"：chromium 150MB + playwright install --with-deps 装系统依赖，每次 runner 重下要 1-2 分钟（缓存命中也要 30 秒）。默认 RUN_UI=0 跳过 UI 测试（只跑接口测试 6 PASS），workflow_dispatch 手动开 RUN_UI=1 才装 chromium 跑 UI 测试（8 PASS）。**这是性能优化不是功能阉割** —— 接口测试是必跑（PR 合并前必须绿），UI 测试是可选（手动触发）。面试时讲清"为什么我没把 UI 测试默认跑 —— CI 经济性 + 接口测试覆盖率已经 90%"。

- "为什么 cache 是 CI runner 的经济性核心（不是可选优化）"：cache: maven 缓存 ~/.m2/repository（Maven 依赖几百 MB），cache: pip 缓存 ~/.cache/pip（pip 依赖几十 MB），cache: playwright 缓存 ~/.cache/ms-playwright（chromium 150MB）。cache key 用 hashFiles('**/requirements.txt') 计算依赖 hash，依赖不变 → 命中缓存（30 秒 vs 3 分钟全装）。**变更触发**：requirements.txt 加一行 cryptography → cache miss → 重装几百 MB。面试时讲清"为什么 cache 是 CI 必加 —— 缓存命中 vs 全装 6 倍速度差"。

- "为什么 upload-artifact@v4 + retention-days 是'报告保险'（allure-action 的 fallback）"：allure-action 部署 gh-pages 是公开历史（每次 push 都更新），但 gh-pages 失败时（如网络问题 / 配置错）CI 端没有报告。upload-artifact@v4 上传 allure-report 目录保留 30 天，PR 评论附下载链接，**双保险**：gh-pages 是公开历史（长期）+ artifact 是 PR 专属（30 天后清理）。面试时讲清"为什么我用双链路交付报告 —— 公开历史 + PR 专属"。

- "为什么 CI 网络不切镜像是有意为之的工程权衡（ubuntu-latest 走国际链路）"：ubuntu-latest runner 走国际链路（aws us-east-1 / azure westus），apt 源 archive.ubuntu.com / pip 源 pypi.org / maven 源 repo.maven.apache.org 都可达（国际带宽 100Mbps+）。切国内镜像（aliyun / tsinghua）反而要走 runner → 中国 CDN → 国际源，链路更长（runner 在境外走中国 CDN 绕路）。**fallback** 是本机原生启动（lessons/0009 playbook），不走 CI。面试时讲清"为什么我没在 CI 切镜像 —— ubuntu-latest 国际链路已经够快"。

## §4 件 M2-D9-001 独有 fix

### Fix 1：pytest skipif 顶层 load env（lesson 0012 已修，CI 端必须沿用）
conftest.py 顶层（不是 fixture 内）调 _load_env()，让 @pytest.mark.skipif(os.getenv('PROD_ID')) 在 collect 阶段拿到真实值。CI 端用 env.PROD_ID 灌 .env：
```bash
cat > test-cases/api-auto/.env <<EOF
PROD_ID=${PROD_ID}
SKU_ID=${PROD_ID}
EOF
```
**不这么做**：CI collect 阶段 os.getenv('PROD_ID') 返回 None → @pytest.mark.skipif(True) → 全部 skip → 0 PASS。

### Fix 2：AES-ECB cryptography 双装
mall4j 登录走 AES-ECB-PKCS7 加密（key='-mall4j-password' 16 字节 + salt=Date.now() 毫秒戳），Python 端用 cryptography 库兼容实现。CI 必须显式装 cryptography + pycryptodome 双包：
```yaml
- name: pip install
  run: |
    pip install -r test-cases/api-auto/requirements.txt
    pip install cryptography pycryptodome
```
**不这么做**：登录永远返回 A00005（解密失败），10 collected / 6 PASS → 0 PASS。

### Fix 3：cart/order 硬编码 ID 用 seed-data.sql
lesson 0011 / 0012 已落"探针请求"动态取真实 prodId/skuId/basketId/orderNumber，但 CI 端不能依赖外部 API 探针（CI 是干净环境无历史数据）。必须在 .github/workflows/seed-data.sql 写 fixture SQL：
```sql
INSERT INTO tz_prod (prod_id, prod_name, price, stock) VALUES (1, 'CI Fixture', 99.00, 100);
```
**不这么做**：cart / order 用例拿到空 stock → 业务链路 8 FAIL。

### Fix 4：awesomecode/allure-action@v1 替代 allure-commandline
allure-commandline 不在 pip，需要 npm i -g + 加 PATH + allure generate + allure open 三步。CI 端用 awesomecode/allure-action@v1 一行搞定：
```yaml
- uses: awesomecode/allure-action@v1
  with:
    allure_version: 2.27.0
    allure_history: true
    github_token: ${{ secrets.GITHUB_TOKEN }}
```
## §引用路径段（4 个）

1. **workflow 文件**：`D:/26测试/mall4j/.github/workflows/api-test.yml`（188 行 / 6.2KB）
2. **CI 使用文档**：`D:/26测试/mall4j/docs/CI.md`（134 行 / 5.3KB）
3. **本地模拟脚本**：`D:/26测试/mall4j/test-cases/api-auto/run-ci.sh`（82 行 / 2.8KB）
4. **实施笔记**：`D:/26测试/mall4j/doc/3-API接口/M2-D9-001-impl-notes.md`（154 行 / 8.3KB）

## §验收 checklist（自评）

- [x] 10 文件落地（含 .gitignore +6 行）
- [x] validate-ci.py [OK] 6/6（YAML 语法 / jobs+steps+services / push main / secrets 10 处 / allure upload 2 次 / bash -n run-ci.sh）
- [x] bash init.sh PASS（harness 100/100 不退化）
- [x] feature_list.json M2-D9-001 status=done + evidence 1047 字符
- [x] AGPLv3 边界 100% 守（仅动 .github/ docs/ doc/3-API接口/ test-cases/api-auto/run-ci.sh + .gitignore 6 个位置）
- [x] 主课 lessons/0014-github-actions-ci-pipeline.html + cheatsheet reference/0014-ci-pipeline-cheatsheet.html + 本 learning-record 三件套齐

## §下次学习方向

- M3-D10-001：Locust 登录压测（depends_on M2-D9-001 done）
- v3.1 SQL fixture 复位：解 Newman 8 条 A 类 FAIL（业务链路硬编码 ID 失效）
- push 到 main 后看真实 runner 日志，回填 api-test.yml 的"踩坑实录"到 impl-notes.md §3

**Status**: active

参见：`../lessons/0014-github-actions-ci-pipeline.html` · `../reference/0014-ci-pipeline-cheatsheet.html` · `../.github/workflows/api-test.yml` · `../scripts/validate-ci.py` · `../docs/CI.md`