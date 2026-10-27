#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立暴力 minimax（与 DP 求解器完全不同的实现）用于交叉验证；并检查 komi 单调性"""
import sys, random
sys.setrecursionlimit(10000)
from functools import lru_cache
import v2_solver as V


def bf_absorb(dmg, s, t, h):
    ab = 0
    while dmg > 0 and h > 0:
        if s > 0: s -= 1; ab += 1
        elif t > 0: t -= 1
        else: h -= 1
        dmg -= 1
    return s, t, h, ab


def bf_value(ply, p, h1, t1, s1, h2, t2, s2, D, CAPT, CAPS, REFLECT, RD, KOMI_UNUSED=None):
    """递归 minimax，返回“当前行动者”视角的 {1,0,-1}"""
    if ply >= D:
        # 到期判分：当前"该行动的一方"是等待方；终止值要给它上一步的行动者，
        # 所以这里返回"等待方"视角，调用处取负
        if p == 1: return dl(h1, t1, s1, h2, t2, s2)
        return dl(h2, t2, s2, h1, t1, s1)
    best = -2
    for a in (0, 1, 2):
        if p == 1: hm, tm, sm, ho, to, so = h1, t1, s1, h2, t2, s2
        else:      hm, tm, sm, ho, to, so = h2, t2, s2, h1, t1, s1
        if a == 0: tm = min(tm + 1, CAPT)
        elif a == 1: sm = min(sm + 2, CAPS)
        else:
            if tm > 0 and ho > 0:
                so, to, ho, ab = bf_absorb(tm, so, to, ho)
                if ho <= 0:
                    best = max(best, 1); continue
                if REFLECT and RD > 0:
                    r = ab // RD
                    if r > 0:
                        sm, tm, hm, _ = bf_absorb(r, sm, tm, hm)
                        if hm <= 0:
                            best = max(best, -1); continue
        if p == 1: nx = (ply+1, 2, hm, tm, sm, ho, to, so)
        else:      nx = (ply+1, 1, ho, to, so, hm, tm, sm)
        v = -bf_value(*nx, D, CAPT, CAPS, REFLECT, RD)
        best = max(best, v)
    return best


def dl(hm, tm, sm, ho, to, so, tie="forces"):
    if hm != ho: return 1 if hm > ho else -1
    if tie == "forces":
        if tm+sm != to+so: return 1 if tm+sm > to+so else -1
    return 0


@lru_cache(maxsize=None)
def bf_cached(st, D, CAPT, CAPS, REFLECT, RD):
    ply, p, h1, t1, s1, h2, t2, s2 = st
    return bf_value(ply, p, h1, t1, s1, h2, t2, s2, D, CAPT, CAPS, REFLECT, RD)


if __name__ == "__main__":
    print("=" * 90)
    print("交叉验证：独立暴力 minimax vs DP 求解器（小配置）")
    print("=" * 90)
    ok = True
    for (H, D, komi, capt, caps, refl, rd) in [
        (2, 6, 1, 4, 8, True, 2), (2, 8, 0, 4, 8, True, 2), (2, 8, 1, 4, 8, False, 2),
        (3, 8, 1, 4, 8, True, 2), (3, 10, 2, 5, 10, True, 3), (3, 12, 0, 5, 10, True, 2),
        (1, 10, 1, 4, 8, True, 2), (4, 10, 1, 5, 10, True, 2),
    ]:
        V.CAPT, V.CAPS = capt, caps
        V.CAPS = caps
        start, layers, vals = V.solve(H=H, KOMI_S=komi, DEADLINE=D, REFLECT=refl,
                                      REFLECT_DIV=rd, verbose=False)
        dp = vals[0][start]
        bf = bf_cached(start, D, capt, caps, refl, rd)
        flag = "OK" if dp == bf else "***不一致***"
        if dp != bf: ok = False
        print(f"  H={H} D={D:<3} komi={komi} CAPT={capt} CAPS={caps} 反击={'开' if refl else '关'}/每{rd}点"
              f"  DP={dp:+d}  BF={bf:+d}  {flag}")
    print(f"\n  交叉验证结论: {'全部一致 ✅' if ok else '存在不一致 ❌'}")
    V.CAPT, V.CAPS = 8, 16

    print()
    print("=" * 90)
    print("单调性检验（给后手更多补偿，先手收益必须不变差）：标量收益")
    print("=" * 90)
    for D in (16, 20, 24, 30):
        vals = []
        for komi in (0, 1, 2, 3, 4):
            s, l, v = V.solve_scalar(KOMI_S=komi, DEADLINE=D, REFLECT=True)
            vals.append(v[0][s])
        mono = all(vals[i] >= vals[i+1] for i in range(len(vals)-1))
        print(f"  预算{D:<3} komi=0..4 标量收益: {vals}  {'单调 ✅' if mono else '非单调 ❌'}")
