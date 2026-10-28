# TurretWar，“炮台战争”简介
持续更新的小游戏，正在进行可视化尝试。

# 编译与运行

各版本都是单文件程序：文件名是 `.cpp`，内容其实是纯 C（同时也能当 C++ 编译）。**注意**：直接 `clang -std=c11 xxx.cpp` 会因为后缀被当成 C++ 而报错，必须显式指定语言。

```bash
# 2.0
clang -x c -std=c11 -O2 -o turretwar2 TurretWar.AlphaTest_2.0.cpp
./turretwar2

# 1.x 同理
clang -x c -std=c11 -O2 -o turretwar1 TurretWar.AlphaTest_1.2.2.cpp

# 也可以用 C++ 编译器
g++ -O2 -o turretwar2 TurretWar.AlphaTest_2.0.cpp

# 关掉 2.0 开场动画的等待（方便测试）
clang -x c -std=c11 -DINTRO_DELAY=0 -o turretwar2 TurretWar.AlphaTest_2.0.cpp
```

（`1.2.1` / `1.2.2` 的源码是 GBK，clang 编译时会提示编码警告，不影响生成可执行文件，详见下方编码说明。）

程序用到 `<unistd.h>` 的 `sleep()`，属于 POSIX 接口：Linux / macOS 可直接编译；Windows 建议用 MinGW 或 WSL，或把相关调用换成 `Sleep()`。

# 编码说明

- UTF-8：`AlphaTest`、`AlphaTest_1.1`、`AlphaTest_1.2`、`AlphaTest_2.0`、`AlphaTest_3.0`、本 README 及文档
- GBK / ANSI：`AlphaTest_1.2.1`、`AlphaTest_1.2.2`（早期在中文 Windows 编辑器下保存）

在 UTF-8 环境里打开后者可能显示乱码；用 MSVC 编译 UTF-8 源文件时请加 `/utf-8`。为保留各版本的原始快照，历史文件未做编码转换。

# 更新日志
## AlphaTest
Published on 2025.3.19
## AlphaTest_1.1
Published on 2025.3.19

更新内容：将轮流行动改为随机行动.
## AlphaTest_1.2
Published on 2025.3.24

更新内容：加入了”再战“选项，并对代码进一步结构化.
## AlphaTest_1.2.1
Published on 2025.3.24

更新内容：通过“有效性检测及清空缓冲区”的手段修复了输入非法字符时偶现的程序崩溃问题.
## AlphaTest_1.2.2
Published on 2025.3.25

更新内容：优化了有效性检测代码，并修复了“提示指令无效重新输入时，没有使该玩家重新输入，而是重新随机”的bug.

## AlphaTest_2.0
Published on 2026.10.15

更新内容：恢复严格轮流行动（移除随机行动），并引入“回合预算”与“护盾反击”两项新机制.
  - 回合预算：双方合计24手；用完时若双方基地都还活着，依次比较 基地生命值 -> 剩余兵力（炮台数+护盾数），仍相同判和棋.
  - 护盾反击：一次进攻中被护盾吸收的每2点伤害，反弹1点给进攻方（击杀优先，反弹不再触发反击）.
  - 后手补偿取消：后手开局1点护盾会补偿过头（经离线求解器验证），故改为0；预算取24手，是因为16手时决策偏向堆护盾，24手起“进攻时机”成为主要决策.
  - 另修复：输入非法字符时的死循环、输入结束后程序自行推进的问题；版本号与伤害统计口径修正.
  - 设计依据与全部实验数据见 RULES-2.0.md 与 SOLVER-REPORT.md（复现脚本在 solver/）.

## AlphaTest_3.0
Published on 2026.10.28

更新内容：引入两个不对称阵营，解决 2.0“平衡只能靠僵持实现”的问题.
  - 壁垒：造护盾+3，炮台伤害1，开局护盾0；突击：造护盾+2，炮台伤害2，开局护盾1（该1点护盾是求解器标定的平衡补偿）.
  - 开局由玩家1选择阵营，玩家2使用另一个；其余规则（严格轮流、24手预算、超时判分、护盾反击）完全沿用2.0.
  - 实测：对局重新出现真实攻防（基地血会被打掉、可以打出击杀），最优走法的多样性是2.0的60~80倍.
  - 已知边界：完美对弈下必有一方必胜（无补偿时壁垒胜，+1护盾后由先手方胜），正式比赛建议双局换边.
  - 设计依据与标定表见 RULES-3.0.md 与 SOLVER-REPORT.md 第十节.
