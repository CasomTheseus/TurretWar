# TurretWar 4.0 · 网页可视化版

规则与 3.0 **完全一致**（壁垒/突击两阵营、严格轮流、24 手预算、超时判分、护盾反击），本目录只是换了呈现方式。

## 打开

```bash
open index.html          # macOS
# 或直接用浏览器打开本文件；无需服务器、无需构建、无外部依赖
```

调试用入口：

| 地址后缀 | 作用 |
|---|---|
| `#demo` | 直接进入一局中盘（双方存活），用于截图/预览 |
| `#autoplay` | 自动走 5 手（走真实交互路径），用于自动化检查；完成后把结果写进 `document.title` |

## 结构

- 单文件 `index.html`：`<style>` 设计令牌与动画、`.app` 布局、`<script id="rules-core">` 规则核、第二个 `<script>` 为 UI/动画层。
- **规则核 `TW`**（`newState / step / judgeDeadline`）是纯函数、不碰 DOM，可由 `module.exports` 在 node 里直接引入。

## 验证方式

规则核与 `solver/v3_factions.py` 的 `stepF`（Python 求解器）逐手对拍：随机阵营 + 随机操作共 200 局，逐手状态、胜者、终局类型全部一致。

> 注意：Python 求解器为了可解性会给炮台/护盾设上限（`CAPT/CAPS`），而游戏本身**没有上限**；对拍时需要把求解器上限抬高，否则护盾超过上限后会出现假性差异。
