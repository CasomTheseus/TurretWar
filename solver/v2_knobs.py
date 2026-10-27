#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""找"既打得起来又平衡"的中间区：候选旋钮 = 基地血 H / 反伤是否伤基地 / 反伤率"""
import time
import v2_solver as V
from v2_solver import step, WIN, DRAW, LOSS


def scan(H=3, KOMI_S=0, DEADLINE=30, rn=1, rd=2, no_base=False):
    start, layers, vals = V.solve(H=H, KOMI_S=KOMI_S, DEADLINE=DEADLINE, REFLECT=True,
                                  REFLECT_DIV=rd, RN=rn, REFLECT_NO_BASE=no_base, verbose=False)
    root = vals[0][start]
    eq = [set() for _ in range(DEADLINE + 1)]
    eq[0].add(start)
    for i in range(DEADLINE):
        for st in eq[i]:
            vv = vals[i][st]
            for a in (0, 1, 2):
                k, payload = step(st, a, DEADLINE, True, "forces", rd, rn, rd, no_base)
                if k == 't': continue
                if -vals[i + 1][payload] == vv: eq[i + 1].add(payload)
    hps = [min(s[2], s[5]) for i in range(DEADLINE + 1) for s in eq[i]]
    return root, (min(hps) if hps else None)


def tag(v): return {WIN: "先手胜", LOSS: "后手胜", DRAW: "和棋"}[v]


if __name__ == "__main__":
    print("=" * 100)
    print("旋钮 A：基地血 H（反伤伤基地, komi=0, 预算30）—— 检验『3 血太少导致二元跳变』的假设")
    print("=" * 100)
    print(f"  {'H':<4}{'反伤率':<12}{'结论':<8}{'均衡最低基地血':<16}")
    for H in (3, 6, 10):
        for rn, rd in ((1, 2), (2, 5), (1, 3)):
            t0 = time.time()
            root, mhp = scan(H=H, rn=rn, rd=rd)
            fight = "有对抗 ✅" if (mhp is not None and mhp < H) else "零基地伤害 ❌"
            print(f"  {H:<4}{f'{rn}/{rd}':<12}{tag(root):<8}{str(mhp)+' '+fight:<16}[{time.time()-t0:.1f}s]")

    print()
    print("=" * 100)
    print("旋钮 B：反伤不伤基地（H=3, komi=0, 预算30）—— 让「进攻不会自杀」")
    print("=" * 100)
    print(f"  {'反伤率':<12}{'结论':<8}{'均衡最低基地血':<16}")
    for rn, rd in ((1, 2), (2, 3), (1, 1)):
        t0 = time.time()
        root, mhp = scan(H=3, rn=rn, rd=rd, no_base=True)
        fight = "有对抗 ✅" if (mhp is not None and mhp < 3) else "零基地伤害 ❌"
        print(f"  {f'{rn}/{rd}':<12}{tag(root):<8}{str(mhp)+' '+fight:<16}[{time.time()-t0:.1f}s]")
