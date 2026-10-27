#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正后：预算只影响「节奏/决策密度」，不影响平衡（komi=0 反击开）"""
import time
from collections import Counter
import v2_solver as V
from v2_solver import step, WIN, DRAW, LOSS


def main():
    print("komi=0, 反伤1/2, H=3 —— 预算对「决策密度」的影响")
    print(f"  {'预算':<5}{'结论':<7}{'可达状态':<11}{'唯一最优占比':<13}"
          f"{'唯一最优分布(炮/盾/攻)':<26}{'均衡集合':<9}")
    for D in (16, 20, 24, 30):
        t0 = time.time()
        start, layers, vals = V.solve(KOMI_S=0, DEADLINE=D, REFLECT=True, verbose=False)
        root = vals[0][start]
        tot = one = 0
        uq = Counter()
        for i in range(D):
            for st, vv in vals[i].items():
                if vv == LOSS:
                    continue
                tot += 1
                keep = []
                for a in (0, 1, 2):
                    k, pl = step(st, a, D, True, "forces", 2, 1, 2, False)
                    c = pl if k == 't' else -vals[i + 1][pl]
                    if c == vv:
                        keep.append(a)
                if len(keep) == 1:
                    one += 1
                    uq[keep[0]] += 1
        eq = [set() for _ in range(D + 1)]
        eq[0].add(start)
        for i in range(D):
            for st in eq[i]:
                vv = vals[i][st]
                for a in (0, 1, 2):
                    k, pl = step(st, a, D, True, "forces", 2, 1, 2, False)
                    if k == 't':
                        continue
                    if -vals[i + 1][pl] == vv:
                        eq[i + 1].add(pl)
        tag = {WIN: "先手胜", LOSS: "后手胜", DRAW: "和棋"}[root]
        print(f"  {D:<5}{tag:<7}{sum(len(l) for l in layers):<11}{f'{100*one/max(tot,1):.1f}%':<13}"
              f"{f'{uq[0]}/{uq[1]}/{uq[2]}':<26}{sum(len(s) for s in eq):<9}[{time.time()-t0:.1f}s]")


if __name__ == "__main__":
    main()
