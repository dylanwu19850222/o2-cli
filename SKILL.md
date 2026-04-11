# O2 CLI - AI Agent 使用指南

**版本**: 0.1.0
**最后更新**: 2026-04-11

---

## 概述

O2 CLI 是一个命令行工具，让 AI agent 可以通过 shell 命令操作 O2 交易平台。所有操作都是对后端 API 的封装。

**安装**（如未安装）:

```bash
pip install o2-cli
```

---

## 核心规则

### 1. `--json` 必须放在命令前面

```bash
# 正确
o2 --json balance show
o2 --json orders list --status open

# 错误（会报 "No such option: --json"）
o2 balance show --json
o2 orders list --status open --json
```

### 2. 需要认证的命令必须先登录

公开命令（无需登录）: `markets list`, `markets orderbook`, `markets candles`, `fees rates`, `fees estimate`

需要登录的命令: `balance`, `orders`, `positions`, `trades`, `deposits`, `withdrawals`, `settings`, `notifications`, `account`

### 3. 返回值都是 JSON

当使用 `--json` 时，输出到 stdout 的是标准 JSON，可以直接用 `jq` 处理或 `json.loads()` 解析。

---

## 快速开始（3 步）

```bash
# 步骤 1: 登录（开发环境用 test-login）
o2 auth test-login
# 输出: token + user info，token 自动保存到 ~/.o2/config.yaml

# 步骤 2: 验证登录成功
o2 --json auth me
# 返回: {"wallet_address": "0x...", "vip_level": 0, ...}

# 步骤 3: 查看余额
o2 --json balance show
# 返回: {"summary": {"total": "...", "withdrawable": "...", "trading": "..."}, ...}
```

---

## 完整命令参考

### 市场数据（公开，无需登录）

```bash
# 市场列表
o2 --json markets list
# 返回: {"markets": [{"marketId": "1", "name": "BTC", "baseToken": "BTC", ...}, ...]}

# 订单簿（BTC = market_id 1, ETH = market_id 2）
o2 --json markets orderbook --market-id 1
# 返回: {"bids": [[price, size], ...], "asks": [[price, size], ...]}

# K线数据
o2 --json markets candles --market-id 1 --interval 1h --limit 100

# 最近成交
o2 --json markets trades --market-id 1 --limit 20

# 手续费率
o2 --json fees rates
# 返回: {"maker_fee_rate": 0.0002, "taker_fee_rate": 0.0005}

# 手续费估算
o2 --json fees estimate --amount 0.001 --price 85000 --is-maker
```

### 认证

```bash
# 开发模式登录（返回测试 token）
o2 --json auth test-login

# 查看当前用户
o2 --json auth me

# 查看 session 状态
o2 --json auth session
```

### 余额

```bash
# 查看余额（现金 + 赠金）
o2 --json balance show
# 返回: {"cash": {"available": "...", "frozen": "..."}, "bonus": {...}, "summary": {...}}

# 余额变更历史
o2 --json balance history --limit 50
```

### 订单

```bash
# 创建市价单（做多 0.001 BTC）
o2 --json orders create --market-id 1 --side long --order-type market --base-amount 0.001

# 创建限价单（做空 0.001 BTC，价格 85000）
o2 --json orders create --market-id 1 --side short --order-type limit --base-amount 0.001 --price 85000

# 带杠杆的限价单（10x 做多）
o2 --json orders create -m 1 -s long -t limit -a 0.001 -p 85000 --leverage 10 --margin-mode cross

# 查询订单
o2 --json orders list
o2 --json orders list --status open        # 仅未成交
o2 --json orders list --market-id 1        # 仅 BTC

# 撤单
o2 --json orders cancel --order-id <ORDER_ID>
o2 --json orders cancel-all                # 撤销所有
o2 --json orders cancel-all --market-id 1  # 仅撤 BTC

# 改单
o2 --json orders modify --order-id <ORDER_ID> --price 86000

# 批量操作（从 JSON 文件）
o2 --json orders batch --file batch_ops.json
# batch_ops.json 格式: [{"action": "create", "side": "long", ...}, {"action": "cancel", "order_id": "..."}]
```

### 持仓

```bash
# 所有持仓
o2 --json positions list

# 特定市场持仓
o2 --json positions market --market-id 1

# 平仓
o2 --json positions close --position-id <POSITION_ID>

# 清算风险评估
o2 --json positions risk --market-id 1
```

### 交易历史

```bash
o2 --json trades list --limit 50
o2 --json trades list --market-id 1
o2 --json trades summary
```

### 充值

```bash
# 获取充值地址
o2 --json deposits address --chain base

# 充值历史
o2 --json deposits history --limit 50
```

### 提币

```bash
# 创建提币
o2 --json withdrawals create --amount 500 --address 0x... --chain ethereum

# 查看提币状态
o2 --json withdrawals status --id <WITHDRAWAL_ID>

# 取消提币（1小时内可取消）
o2 --json withdrawals cancel --id <WITHDRAWAL_ID>

# 提币历史
o2 --json withdrawals list
```

### 用户设置

```bash
# 查看当前设置
o2 --json settings get

# 设置杠杆（BTC 10x）
o2 --json settings leverage --market-id 1 --leverage 10

# 设置保证金模式（cross=全仓, isolated=逐仓）
o2 --json settings margin-mode --mode cross
```

### 通知

```bash
o2 --json notifications list
o2 --json notifications unread
o2 --json notifications read --id <NOTIFICATION_ID>
```

### 账户总览

```bash
o2 --json account overview
# 返回: 余额 + 持仓 + 风险信息的综合视图
```

### 做市商（需要 API Key）

```bash
o2 --json mm status           # 做市商状态
o2 --json mm start            # 启动
o2 --json mm stop             # 停止
o2 --json mm stats            # 统计
o2 --json mm orders           # 当前挂单
```

### 管理员（需要 admin JWT）

```bash
o2 --json admin gas-status
o2 --json admin proxy-list
o2 --json admin api-keys
o2 --json admin reconcile
```

---

## 参数速查

| 参数 | 含义 | 可选值 |
|------|------|--------|
| `--market-id` / `-m` | 市场ID | 1=BTC, 2=ETH |
| `--side` / `-s` | 方向 | `long`, `short` |
| `--order-type` / `-t` | 订单类型 | `market`, `limit` |
| `--base-amount` / `-a` | 数量 | 如 `0.001`（BTC 单位） |
| `--price` / `-p` | 价格 | 如 `85000`（USDC） |
| `--leverage` / `-l` | 杠杆 | 1-50 |
| `--margin-mode` | 保证金模式 | `cross`, `isolated` |
| `--status` | 订单状态过滤 | `open`, `filled`, `cancelled`, `all` |
| `--limit` / `-n` | 返回数量 | 数字，默认 50 |
| `--chain` | 区块链 | `base`, `ethereum`, `arbitrum` |

---

## 典型工作流

### Agent 工作流 1: 检查账户状态

```bash
o2 auth test-login
o2 --json balance show
o2 --json positions list
o2 --json orders list --status open
```

### Agent 工作流 2: 开仓 + 设止损

```bash
# 1. 市价做多 0.001 BTC
o2 --json orders create -m 1 -s long -t market -a 0.001
# 拿到 order_id，等待成交

# 2. 确认持仓
o2 --json positions list

# 3. 设置杠杆
o2 --json settings leverage --market-id 1 --leverage 10
```

### Agent 工作流 3: 检查风险并平仓

```bash
# 1. 检查清算风险
o2 --json positions risk --market-id 1

# 2. 查看当前价格
o2 --json markets orderbook --market-id 1

# 3. 平仓
o2 --json positions close --position-id <ID>
```

### Agent 工作流 4: 提币

```bash
# 1. 检查余额
o2 --json balance show

# 2. 发起提币
o2 --json withdrawals create --amount 100 --address 0xYourAddress --chain base

# 3. 查看提币状态
o2 --json withdrawals status --id <WITHDRAWAL_ID>
```

---

## 错误处理

CLI 遵循标准退出码:
- `0` = 成功
- `1` = 错误（API 错误、网络错误、认证失败等）

使用 `--json` 时，错误输出到 stderr:
```json
{"error": "Not authenticated. Run 'o2 auth test-login' first.", "code": null}
```

数据输出到 stdout。所以可以安全地:
```bash
result=$(o2 --json balance show 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "余额: $result"
else
    echo "获取失败"
fi
```

---

## 配置文件

位置: `~/.o2/config.yaml`

```yaml
active_profile: default
profiles:
  default:
    api_url: http://localhost:8000/api/v1
    timeout: 30
    auth_type: jwt
    token: eyJ...  # 自动保存
    default_market_id: 1
    default_chain: base
```

切换环境:
```bash
o2 --profile production --json balance show
o2 --api-url https://api.o2-dex.com/api/v1 --json markets list
```

---

## Skill 安装（给 Vibe Coding 工具）

```bash
# 交互式安装（选择你的工具和范围）
o2 setup

# 非交互式
o2 setup --tool claude-code --scope global
o2 setup --tool cursor --scope project

# 更新所有已安装工具的 skill 文件
o2 setup --update

# 查看安装状态
o2 setup --status
```

支持的工具: Claude Code, Cursor, Codex, Windsurf, Cline, Trae

---

## 注意事项

1. **token 会过期** — 如果命令返回认证错误，重新运行 `o2 auth test-login`
2. **market_id** — BTC = 1, ETH = 2，用 `o2 markets list` 查看所有市场
3. **数量单位** — `--base-amount` 是实际数量（如 0.001 BTC），不是合约单位
4. **side 必须是 long/short** — 不是 buy/sell
5. **--json 放命令前面** — 这是 Typer 的全局选项位置要求

---

## 故障排查

| 问题 | 解决方法 |
|------|----------|
| `Cannot connect to localhost:8000` | 后端未启动，确认 O2 Backend 正在运行 |
| `Not authenticated` | 运行 `o2 auth test-login` |
| `No such option: --json` | 把 `--json` 移到 `o2` 后面，子命令前面 |
| `o2: command not found` | 运行 `pip install o2-cli` |

---

## 技术架构

```
o2 CLI (Typer + Rich + httpx)
    |
    |-- ~/.o2/config.yaml  <- token / profile 管理
    |
    +-- HTTP -> O2 Backend (FastAPI)
         |-- /api/v1/auth/*       <- JWT 认证
         |-- /api/v1/balance/*    <- 余额查询
         |-- /api/v1/orders/*     <- 订单管理
         |-- /api/v1/positions/*  <- 持仓管理
         |-- /api/v1/markets/*    <- 市场数据
         +-- ... (100+ 端点)
```

**API 响应格式**: `{"success": true, "data": {...}, "error": null, "code": null, "timestamp": "..."}`

CLI 自动解包 `data` 字段，`--json` 直接输出 `data` 内容。

---

**生成时间**: 2026-04-11
**维护者**: Dylan + Claude
