#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""二维搜索：反伤比例 × 到期判分口径。目标：找到"没有一方能强制取胜"且"均衡路径上真的打得掉基地血"的参数区"""
import sys, time
from fractions import Fraction
import v2_solver as V
from v2_solver import step, WIN, DRAW, LOSS, NAME


def scan(KOMI_S=0, DEADLINE=30, RN=1, RD=2, REFLECT=True, TIE="forces", H=3):
    start, layers, vals = V.solve(H=H, KOMI_S=KOMI_S, DEADLINE=DEADLINE, REFLECT=REFLECT,
                                  TIE=TIE, REFLECT_DIV=RD, RN=RN, verbose=False)
    root = vals[0][start]
    eq = [set() for _ in range(DEADLINE + 1)]
    eq[0].add(start)
    for i in range(DEADLINE):
        for st in eq[i]:
            vv = vals[i][st]
            for a in (0, 1, 2):
                kind, payload = step(st, a, DEADLINE, REFLECT, TIE, RD, RN, RD)
                if kind == 't': continue
                if -vals[i + 1][payload] == vv: eq[i + 1].add(payload)
    hps = [min(s[2], s[5]) for i in range(DEADLINE + 1) for s in eq[i]]
    return root, (min(hps) if hps else None), sum(len(s) for s in eq)


def tag(v): return {WIN: "先手胜", LOSS: "后手胜", DRAW: "和棋"}[v]


if __name__ == "__main__":
    print("=" * 104)
    print("反伤比例 × 判分口径（komi=0, 预算30, H=3）  均衡最低基地血=3 表示『谁都没打掉过血』")
    print("=" * 104)
    for tie, tie_name in (("forces", "比基地血→比兵力"), ("none", "只比基地血(血平即和)")):
        print(f"\n  ■ 判分口径：{tie_name}")
        print(f"    {'反伤比例':<12}{'结论':<8}{'均衡最低基地血':<16}{'均衡集合':<10}")
        for rn, rd in ((0, 1), (1, 4), (3, 10), (2, 7), (1, 3), (2, 5), (1, 2), (3, 5), (2, 3)):
            t0 = time.time()
            root, mhp, eqn = scan(KOMI_S=0, RN=rn, RD=rd, REFLECT=(rn > 0), TIE=tie)
            rate = "关闭" if rn == 0 else f"{rn}/{rd}={rn/rd:.3f}"
            fight = "有对抗 ✅" if (mhp is not None and mhp < 3) else "零基地伤害(僵持) ❌"
            print(f"    {rate:<12}{tag(root):<8}{str(mhp)+' '+fight:<16}{eqn:<10}[{time.time()-t0:.1f}s]")
