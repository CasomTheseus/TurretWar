#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机制对照实验：哪些改动能消除"先手必胜"？
参数化求解（吸引子算法，三值胜负）：
  H           基地血（当前 3）
  SH          每次造护盾获得量（当前 2）
  KOMI_S/KOMI_T  后手方开局额外护盾/炮台（先手补偿，当前 0/0）
  TURRET_COST 每次进攻消耗攻方炮台数（当前 0 = 炮台可重复使用）
输出：开局让先手方是否必胜 + 取胜所需手数 + CAP 自检。
"""
import sys, time
from collections import deque

T, S, A = 0, 1, 2


def attack(t_atk, s_def, t_def, h_def):
    dmg = t_atk
    while dmg > 0 and h_def > 0:
        if s_def > 0: s_def -= 1
        elif t_def > 0: t_def -= 1
        else: h_def -= 1
        dmg -= 1
    return s_def, t_def, h_def


def solve(H, CAP, SH=2, KOMI_S=0, KOMI_T=0, TURRET_COST=0, verbose=False):
    idx, states = {}, []
    for p in (1, 2):
        for h1 in range(1, H + 1):
            for h2 in range(1, H + 1):
                for t1 in range(CAP + 1):
                    for s1 in range(CAP + 1):
                        for t2 in range(CAP + 1):
                            for s2 in range(CAP + 1):
                                idx[(p, h1, t1, s1, h2, t2, s2)] = len(states)
                                states.append((p, h1, t1, s1, h2, t2, s2))
    N = len(states)
    succ = [None] * N
    rev = [[] for _ in range(N)]
    for i, st in enumerate(states):
        p, h1, t1, s1, h2, t2, s2 = st
        mv = []
        if p == 1:
            mv.append(('s', idx[(2, h1, min(t1 + 1, CAP), s1, h2, t2, s2)]))
            mv.append(('s', idx[(2, h1, t1, min(s1 + SH, CAP), h2, t2, s2)]))
            s2n, t2n, h2n = attack(t1, s2, t2, h2)
            if h2n <= 0:
                mv.append(('w1',))
            else:
                mv.append(('s', idx[(2, h1, max(0, t1 - TURRET_COST), s1, h2n, t2n, s2n)]))
        else:
            mv.append(('s', idx[(1, h1, t1, s1, h2, min(t2 + 1, CAP), s2)]))
            mv.append(('s', idx[(1, h1, t1, s1, h2, t2, min(s2 + SH, CAP))]))
            s1n, t1n, h1n = attack(t2, s1, t1, h1)
            if h1n <= 0:
                mv.append(('w2',))
            else:
                mv.append(('s', idx[(1, h1n, t1n, s1n, h2, max(0, t2 - TURRET_COST), s2)]))
        succ[i] = mv
        for kind, *rest in mv:
            if kind == 's':
                rev[rest[0]].append(i)

    def attractor(who):
        term = 'w1' if who == 1 else 'w2'
        inm = bytearray(N); rank = [-1] * N
        cnt = [0] * N
        for i, st in enumerate(states):
            if st[0] != who: cnt[i] = 3
        q = deque()
        for i, st in enumerate(states):
            if st[0] == who:
                for kind, *r in succ[i]:
                    if kind == term:
                        inm[i] = 1; rank[i] = 0; q.append(i); break
        while q:
            j = q.popleft()
            for i in rev[j]:
                if inm[i]: continue
                if states[i][0] == who:
                    inm[i] = 1; rank[i] = rank[j] + 1; q.append(i)
                else:
                    cnt[i] -= 1
                    if cnt[i] == 0:
                        inm[i] = 1; rank[i] = rank[j] + 1; q.append(i)
        return inm, rank

    a1, r1 = attractor(1)
    a2, r2 = attractor(2)

    def verdict(mover):
        """mover 先手；KOMI 恒定给后手方。返回 (先手方视角结论, 取胜手数)"""
        if mover == 1:   # 玩家1先手，P2 是后手 -> komi 给 P2
            st = (1, H, 0, 0, H, KOMI_T, KOMI_S)
            mine, theirs = a1, a2
        else:            # 玩家2先手，P1 是后手 -> komi 给 P1
            st = (2, H, KOMI_T, KOMI_S, H, 0, 0)
            mine, theirs = a2, a1
        i = idx[st]
        if mine[i]:   return "先手方必胜", (r1 if mover == 1 else r2)[i]
        if theirs[i]: return "先手方必败(后手必胜)", (r2 if mover == 1 else r1)[i]
        return "和(双方都无法必胜)", None

    v1, k1 = verdict(1)
    v2, k2 = verdict(2)
    consistent = (v1 == v2)
    # CAP 自检：从先手必胜局面抽一条最短取胜线路
    maxt = maxs = 0
    if v1 == "先手方必胜":
        st = (1, H, 0, 0, H, KOMI_T, KOMI_S)
        plies = 0
        while plies < 500:
            p, h1, t1, s1, h2, t2, s2 = st
            maxt = max(maxt, t1 if p == 1 else t2); maxs = max(maxs, s1 if p == 1 else s2)
            i = idx[st]; best = None
            for a, (kind, *rest) in enumerate(succ[i]):
                if kind == 'w1': cand = (0 if p == 1 else 10**9, a, None)
                elif a1[rest[0]]:
                    cand = (r1[rest[0]], a, rest[0]) if p == 1 else (-r1[rest[0]], a, rest[0])
                else: continue
                if best is None or cand[0] < best[0]: best = cand
            if best is None: break
            _, a, nxt = best
            plies += 1
            if nxt is None: break
            st = states[nxt]
    if verbose:
        print(f"    [N={N}]")
    return dict(v1=v1, k1=k1, v2=v2, consistent=consistent, maxt=maxt, maxs=maxs, N=N)


if __name__ == "__main__":
    print("=========== 实验 A（结论：先手方=先行动的一方）：基地血 H 扫描（其余为当前规则）===========")
    print("H   | 先手结论         | 取胜手数 | 线上最大炮台/护盾 | CAP自检")
    for H in (2, 3, 4, 5, 6):
        r = solve(H, CAP=8 if H <= 4 else 10)
        ok = "成立" if (r['maxt'] < (8 if H <= 4 else 10) and r['maxs'] < (8 if H <= 4 else 10)) else "触上限!"
        print(f"{H:<3} | {r['v1']:<14} | {str(r['k1']):<8} | {r['maxt']}/{r['maxs']:<14} | {ok}   (对称自检:{'通过' if r['consistent'] else '失败'})")

    print()
    print("=========== 实验 B：给后手方开局补偿（先手补偿 komi），H=3 ===========")
    print("后手起始护盾 | 后手起始炮台 | 先手结论         | 取胜手数")
    for ks in (0, 1, 2, 3, 4, 5, 6):
        r = solve(3, CAP=10, KOMI_S=ks)
        print(f"{ks:<12} | {0:<12} | {r['v1']:<14} | {r['k1']}")
    for kt in (1, 2):
        r = solve(3, CAP=10, KOMI_T=kt)
        print(f"{0:<12} | {kt:<12} | {r['v1']:<14} | {r['k1']}")

    print()
    print("=========== 实验 C：护盾强度 SH（当前 2），H=3 ===========")
    for sh in (1, 2, 3, 4):
        r = solve(3, CAP=10, SH=sh)
        print(f"造护盾 +{sh}: {r['v1']}")

    print()
    print("=========== 实验 D：让炮台在进攻后被消耗（TURRET_COST），H=3 ===========")
    for tc in (1, 2):
        r = solve(3, CAP=10, TURRET_COST=tc)
        print(f"每次进攻消耗 {tc} 座炮台: {r['v1']}")
