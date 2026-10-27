#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TurretWar 当前规则（严格轮流、基地3血）的正确求解与结构诊断。
用标准吸引子(attractor)算法求三值胜负：胜/和/负，有环也不会偏向任何一方。
CAP = 炮台/护盾数量上限（把无限状态空间截断）。脚本会检查"最短取胜策略"
用到的最大炮台/护盾数，判断 CAP 是否失真。
"""
import sys
from collections import deque

T, S, A = 0, 1, 2
NAMES = {T: "造炮台", S: "造护盾", A: "进攻"}


def attack(t_atk, s_def, t_def, h_def):
    dmg = t_atk
    while dmg > 0 and h_def > 0:
        if s_def > 0: s_def -= 1
        elif t_def > 0: t_def -= 1
        else: h_def -= 1
        dmg -= 1
    return s_def, t_def, h_def


def build(H, CAP):
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
            mv.append(('s', idx[(2, h1, t1, min(s1 + 2, CAP), h2, t2, s2)]))
            s2n, t2n, h2n = attack(t1, s2, t2, h2)
            mv.append(('w1',) if h2n <= 0 else ('s', idx[(2, h1, t1, s1, h2n, t2n, s2n)]))
        else:
            mv.append(('s', idx[(1, h1, t1, s1, h2, min(t2 + 1, CAP), s2)]))
            mv.append(('s', idx[(1, h1, t1, s1, h2, t2, min(s2 + 2, CAP))]))
            s1n, t1n, h1n = attack(t2, s1, t1, h1)
            mv.append(('w2',) if h1n <= 0 else ('s', idx[(1, h1n, t1n, s1n, h2, t2, s2)]))
        succ[i] = mv
        for kind, *rest in mv:
            if kind == 's':
                rev[rest[0]].append(i)
    return states, idx, succ, rev


def attractor(states, succ, rev, who):
    """who=1/2: 求该玩家的必胜状态集与取胜所需手数(秩)"""
    N = len(states)
    term = 'w1' if who == 1 else 'w2'
    inm = bytearray(N)
    rank = [-1] * N
    cnt = [0] * N
    for i, st in enumerate(states):
        if st[0] != who:
            cnt[i] = 3                      # 对手节点：3 个走法都要落进吸引集
    q = deque()
    for i, st in enumerate(states):
        if st[0] == who:
            for kind, *rest in succ[i]:
                if kind == term:
                    inm[i] = 1; rank[i] = 0; q.append(i); break
    while q:
        j = q.popleft()
        for i in rev[j]:
            if inm[i]:
                continue
            if states[i][0] == who:
                inm[i] = 1; rank[i] = rank[j] + 1; q.append(i)
            else:
                cnt[i] -= 1
                if cnt[i] == 0:
                    inm[i] = 1; rank[i] = rank[j] + 1; q.append(i)
    return inm, rank


def analyse(H=3, CAP=8):
    states, idx, succ, rev = build(H, CAP)
    N = len(states)
    a1, r1 = attractor(states, succ, rev, 1)
    a2, r2 = attractor(states, succ, rev, 2)
    overlap = sum(1 for i in range(N) if a1[i] and a2[i])
    start1 = idx[(1, H, 0, 0, H, 0, 0)]
    start2 = idx[(2, H, 0, 0, H, 0, 0)]
    v1 = '玩家1必胜' if a1[start1] else ('玩家1必败' if a2[start1] else '和(双方都无法必胜)')
    v2 = '玩家2必胜' if a2[start2] else ('玩家2必败' if a1[start2] else '和(双方都无法必胜)')
    print(f"===== 基地血={H}  CAP={CAP}  状态数={N}  双方必胜区重叠={overlap}(应为0) =====")
    print(f"  开局玩家1先手: {v1}   取胜所需手数(秩)={r1[start1]}")
    print(f"  开局玩家2先手: {v2}   取胜所需手数(秩)={r2[start2]}")
    # 对称性自检：把玩家1先手的结论按标签互换应当一致
    print(f"  [对称性自检] 两种先手结论是否一致: {'一致' if (a1[start1] and a2[start2]) or (not a1[start1] and not a2[start2] and not a1[start2] and not a2[start1]) else '不一致'}")

    # 赢方节点的"决策精度"：随便走都赢 vs 只有部分走法保住胜利
    if a1[start1]:
        win, crit_one, free_all, total = 1, 0, 0, 0
        for i, st in enumerate(states):
            if st[0] != 1 or not a1[i]:
                continue
            total += 1
            keep = 0
            for kind, *rest in succ[i]:
                if kind == 'w1':
                    keep += 1
                elif a1[rest[0]]:
                    keep += 1
            if keep == 3: free_all += 1
            if keep == 1: crit_one += 1
        print(f"  玩家1必胜区中『轮到玩家1』的局面 {total} 个：")
        print(f"    三种走法都仍必胜(随便走): {free_all} ({100*free_all/total:.1f}%)")
        print(f"    只有一种走法能保住胜利(关键决策): {crit_one} ({100*crit_one/total:.1f}%)")

    # 抽取最短取胜策略，检查 CAP 是否绑定
    st = states[start1]; plies = 0; maxt = maxs = 0; line = []
    while True:
        p, h1, t1, s1, h2, t2, s2 = st
        maxt = max(maxt, t1 if p == 1 else t2)
        maxs = max(maxs, s1 if p == 1 else s2)
        i = idx[st]
        best = None
        for a, (kind, *rest) in enumerate(succ[i]):
            if kind == 'w1':
                cand = (0, a, None)
            elif a1[rest[0]]:
                cand = (r1[rest[0]] + (1 if p == 1 else -1), a, rest[0])   # p1取小, p2取大(拖延)
            else:
                continue
            if best is None or (p == 1 and cand[0] < best[0]) or (p == 2 and cand[0] > best[0]):
                best = cand
        if best is None:
            break
        _, a, nxt = best
        line.append(f"{'P%d' % p}{NAMES[a]}")
        plies += 1
        if nxt is None or plies > 400:
            break
        st = states[nxt]
    print(f"  一条最短取胜线路: {plies} 手, 线上最大炮台={maxt}, 最大护盾={maxs}  (CAP={CAP})")
    print(f"  [CAP 自检] 线上最大值 {'远小于' if maxt < CAP and maxs < CAP else '触到'} 上限", 
          "-> 结论对无上限原版同样成立" if maxt < CAP and maxs < CAP else "-> 结论可能被上限扭曲，需增大 CAP")
    print(f"  线路前 20 手: {' '.join(line[:20])}")
    print()
    return dict(v1=v1, rank=r1[start1], maxt=maxt, maxs=maxs)


if __name__ == "__main__":
    for cap in (6, 8, 10):
        analyse(3, cap)
