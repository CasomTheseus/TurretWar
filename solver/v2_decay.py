#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A2-①：护盾衰减（shield decay）能否打破 2.0 的"平衡 ⟺ 僵持"？

机制：每回合开始时，**行动方自身护盾 -DECAY**（不低于 0），然后再执行行动。
      等价于"每位玩家的护盾每轮衰减 DECAY 点"。

判据：
  - 结论 = 和棋         -> 没有一方能强制取胜（平衡）
  - 均衡最低基地血 < 3   -> 均衡路径上真的打到基地了（有对抗）
  两者同时成立 = 目标达成

另外报告均衡路径上的行动分布，用来确认"造护盾"没有被废掉。
"""
import time
from collections import defaultdict
import v2_solver as V
from v2_solver import step, WIN, DRAW, LOSS, NAME

H = 3


def analyse(KOMI_S=0, DEADLINE=24, RN=1, RD=2, REFLECT=True, DECAY=0):
    start, layers, vals = V.solve(KOMI_S=KOMI_S, DEADLINE=DEADLINE, REFLECT=REFLECT,
                                  REFLECT_DIV=RD, RN=RN, DECAY=DECAY, verbose=False)
    root = vals[0][start]
    eq = [set() for _ in range(DEADLINE + 1)]
    eq[0].add(start)
    for i in range(DEADLINE):
        for st in eq[i]:
            vv = vals[i][st]
            for a in (0, 1, 2):
                k, pl = step(st, a, DEADLINE, REFLECT, "forces", RD, RN, RD, False, DECAY)
                if k == 't':
                    continue
                if -vals[i + 1][pl] == vv:
                    eq[i + 1].add(pl)
    cnt = defaultdict(int)
    for i in range(DEADLINE):
        for st in eq[i]:
            vv = vals[i][st]
            for a in (0, 1, 2):
                k, pl = step(st, a, DEADLINE, REFLECT, "forces", RD, RN, RD, False, DECAY)
                if k == 't':
                    if pl == vv and pl == WIN:
                        cnt[a] += 1
                    continue
                if -vals[i + 1][pl] == vv:
                    cnt[a] += 1
    hps = [min(s[2], s[5]) for i in range(DEADLINE + 1) for s in eq[i]]
    mt = max(max(s[3], s[6]) for i in range(DEADLINE + 1) for s in eq[i])
    ms = max(max(s[4], s[7]) for i in range(DEADLINE + 1) for s in eq[i])
    tot = sum(cnt.values()) or 1
    return dict(root=root, min_hp=min(hps) if hps else None, eq=sum(len(s) for s in eq),
                shares=(cnt[0] / tot, cnt[1] / tot, cnt[2] / tot), maxt=mt, maxs=ms)


def tag(v):
    return {WIN: "先手胜", LOSS: "后手胜", DRAW: "和棋"}[v]


def row(label, **kw):
    t0 = time.time()
    d = analyse(**kw)
    ok = "✅目标" if (d['root'] == DRAW and d['min_hp'] is not None and d['min_hp'] < H) else ""
    sh = d['shares']
    print(f"  {label:<24}{tag(d['root']):<7} 均衡最低基地血={str(d['min_hp']):<3}"
          f"{'有对抗' if (d['min_hp'] is not None and d['min_hp'] < H) else '无基地伤害':<12}"
          f" 均衡集合={d['eq']:<7} 行动占比 炮{sh[0]*100:4.0f}%/盾{sh[1]*100:4.0f}%/攻{sh[2]*100:4.0f}%"
          f" 峰值炮/盾={d['maxt']}/{d['maxs']} {ok} [{time.time()-t0:.1f}s]")
    return d


if __name__ == "__main__":
    print("=" * 128)
    print("A2-① 护盾衰减扫描（H=3, 预算24=2.0 定稿, komi=0）")
    print("  判据：结论=和棋（平衡）且 均衡最低基地血<3（真打）。同时看『造护盾』有没有被废掉")
    print("=" * 128)
    for decay in (0, 1, 2):
        print(f"\n  ■ DECAY={decay}（每回合自身护盾 -{decay}）")
        for label, kw in (
            ("反击关闭",        dict(REFLECT=False)),
            ("反击 1/4",        dict(RN=1, RD=4)),
            ("反击 1/3",        dict(RN=1, RD=3)),
            ("反击 1/2(2.0定稿)", dict(RN=1, RD=2)),
        ):
            row(label, DECAY=decay, DEADLINE=24, **kw)
