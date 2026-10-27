#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A2 后续：永久升级（permanent upgrade）能否打破「平衡 ⟺ 僵持」？

机制（第 4 种行动）：
  - 「升级」：每位玩家最多一次，永久生效；
  - 升级后每座炮台的伤害从 1 变为 2（damage = 炮台数 × (1 + up)）；
  - 其余规则同 2.0（严格轮流、24 手预算、超时判分、护盾反击）。

设计意图：这是本游戏里第一个**不可逆**的投资（炮台/护盾都能重建，等级不能回退）。

判据同前：
  - 结论 = 和棋            -> 没有一方能强制取胜（平衡）
  - 均衡最低基地血 < H      -> 均衡路径上真的打到基地了（有对抗）
  两者同时成立 = 目标达成

本模块不改动 v2_solver.py（已发布的脚本依赖它的 3 行动接口）。
ALLOW_UP=False 时必须与 v2_solver.solve 的结果完全一致 —— 用作自检。
"""
import time
from collections import defaultdict
from v2_solver import shield_absorb, WIN, DRAW, LOSS

CAPT, CAPS = 8, 16
H = 3
NAME4 = {0: "造炮台", 1: "造护盾", 2: "进攻", 3: "升级"}


def init4(H=3, KOMI_S=0):
    return (0, 1, H, 0, 0, 0, H, KOMI_S, 0, 0)   # ply,p,h1,t1,s1,u1,h2,t2,s2,u2


def deadline_value(h_m, t_m, s_m, h_o, t_o, s_o):
    if h_m != h_o:
        return WIN if h_m > h_o else LOSS
    f_m, f_o = t_m + s_m, t_o + s_o
    if f_m != f_o:
        return WIN if f_m > f_o else LOSS
    return DRAW


def step4(st, a, D, REFLECT=True, RN=1, RD=2, ALLOW_UP=True):
    """返回 (kind, payload)；kind=='x' 表示该行动在此局面不合法（调用者跳过）"""
    ply, p, h1, t1, s1, u1, h2, t2, s2, u2 = st
    if p == 1:
        h_m, t_m, s_m, u_m = h1, t1, s1, u1
        h_o, t_o, s_o, u_o = h2, t2, s2, u2
    else:
        h_m, t_m, s_m, u_m = h2, t2, s2, u2
        h_o, t_o, s_o, u_o = h1, t1, s1, u1

    if a == 0:
        t_m = min(t_m + 1, CAPT)
    elif a == 1:
        s_m = min(s_m + 2, CAPS)
    elif a == 3:
        if not ALLOW_UP or u_m:
            return ('x', None)                  # 不能升级 / 已升级过
        u_m = 1
    else:
        dmg = t_m * (1 + u_m)                   # 升级后每座炮台 2 点伤害
        if dmg > 0 and h_o > 0:
            _, s_o, t_o, h_o, absorbed = shield_absorb(dmg, s_o, t_o, h_o)
            if h_o <= 0:
                return ('t', WIN)
            if REFLECT:
                refl = absorbed * RN // RD
                if refl > 0:
                    _, s_m, t_m, h_m, _ = shield_absorb(refl, s_m, t_m, h_m)
                    if h_m <= 0:
                        return ('t', LOSS)

    if p == 1:
        new = (ply + 1, 2, h_m, t_m, s_m, u_m, h_o, t_o, s_o, u_o)
    else:
        new = (ply + 1, 1, h_o, t_o, s_o, u_o, h_m, t_m, s_m, u_m)

    if ply + 1 >= D:
        ply2, p2, h1n, t1n, s1n, u1n, h2n, t2n, s2n, u2n = new
        if p2 == 1:
            v = deadline_value(h1n, t1n, s1n, h2n, t2n, s2n)
        else:
            v = deadline_value(h2n, t2n, s2n, h1n, t1n, s1n)
        return ('t', -v)
    return ('s', new)


ACTIONS = (0, 1, 2, 3)


def solve4(D=24, KOMI_S=0, REFLECT=True, RN=1, RD=2, ALLOW_UP=True, verbose=False):
    start = init4(H, KOMI_S)
    layers = [{start}]
    cur = layers[0]
    for _ in range(D):
        nxt = set()
        for st in cur:
            for a in ACTIONS:
                kind, payload = step4(st, a, D, REFLECT, RN, RD, ALLOW_UP)
                if kind == 's':
                    nxt.add(payload)
        layers.append(nxt)
        cur = nxt
    vals = [None] * (D + 1)
    vals[D] = {}
    for st in layers[D]:
        ply, p, h1, t1, s1, u1, h2, t2, s2, u2 = st
        if p == 1:
            vals[D][st] = deadline_value(h1, t1, s1, h2, t2, s2)
        else:
            vals[D][st] = deadline_value(h2, t2, s2, h1, t1, s1)
    for k in range(D - 1, -1, -1):
        v = {}
        for st in layers[k]:
            best = -2
            for a in ACTIONS:
                kind, payload = step4(st, a, D, REFLECT, RN, RD, ALLOW_UP)
                if kind == 'x':
                    continue
                cand = payload if kind == 't' else -vals[k + 1][payload]
                if cand > best:
                    best = cand
            v[st] = best
        vals[k] = v
    if verbose:
        print(f"    [solve4] 可达状态总数={sum(len(l) for l in layers)} "
              f"最大单层={max(len(l) for l in layers)}")
    return start, layers, vals


def analyse(D=24, KOMI_S=0, REFLECT=True, RN=1, RD=2, ALLOW_UP=True):
    start, layers, vals = solve4(D, KOMI_S, REFLECT, RN, RD, ALLOW_UP)
    root = vals[0][start]
    eq = [set() for _ in range(D + 1)]
    eq[0].add(start)
    for i in range(D):
        for st in eq[i]:
            vv = vals[i][st]
            for a in ACTIONS:
                kind, payload = step4(st, a, D, REFLECT, RN, RD, ALLOW_UP)
                if kind != 's':
                    continue
                if -vals[i + 1][payload] == vv:
                    eq[i + 1].add(payload)
    cnt = defaultdict(int)
    for i in range(D):
        for st in eq[i]:
            vv = vals[i][st]
            for a in ACTIONS:
                kind, payload = step4(st, a, D, REFLECT, RN, RD, ALLOW_UP)
                if kind == 'x':
                    continue
                if kind == 't':
                    if payload == vv and payload == WIN:
                        cnt[a] += 1
                    continue
                if -vals[i + 1][payload] == vv:
                    cnt[a] += 1
    hps = [min(s[2], s[6]) for i in range(D + 1) for s in eq[i]]
    tot = sum(cnt.values()) or 1
    return dict(root=root, min_hp=min(hps) if hps else None,
                eq=sum(len(s) for s in eq), reach=sum(len(l) for l in layers),
                shares=tuple(cnt[a] / tot for a in ACTIONS))


def tag(v):
    return {WIN: "先手胜", LOSS: "后手胜", DRAW: "和棋"}[v]


if __name__ == "__main__":
    print("=" * 118)
    print("自检：关闭升级（ALLOW_UP=False）时必须与 v2_solver 的结果一致")
    print("=" * 118)
    import v2_solver as V
    for D, komi, refl, rn, rd in ((16, 0, True, 1, 2), (16, 1, False, 1, 2), (20, 0, True, 1, 3)):
        _, _, v4 = solve4(D=D, KOMI_S=komi, REFLECT=refl, RN=rn, RD=rd, ALLOW_UP=False)
        s, l, v3 = V.solve(KOMI_S=komi, DEADLINE=D, REFLECT=refl, RN=rn, REFLECT_DIV=rd, verbose=False)
        a4 = v4[0][init4(H, komi)]
        a3 = v3[0][s]
        print(f"  D={D:<3} komi={komi} 反击={'开' if refl else '关'}/{rn}/{rd}: "
              f"solve4={a4:+d}  v2_solver={a3:+d}  {'OK' if a4 == a3 else '***不一致***'}")

    print()
    print("=" * 118)
    print("永久升级实验（H=3, 预算24, komi=0）")
    print("=" * 118)
    print(f"  {'配置':<26}{'结论':<7}{'均衡最低基地血':<16}{'可达状态':<10}"
          f"{'均衡集合':<9}{'行动占比 炮/盾/攻/升'}")
    for allow in (False, True):
        for label, refl in (("反击关闭", False), ("反击 1/2", True)):
            t0 = time.time()
            d = analyse(D=24, KOMI_S=0, REFLECT=refl, ALLOW_UP=allow)
            fight = "有对抗" if (d['min_hp'] is not None and d['min_hp'] < H) else "零基地伤害"
            sh = d['shares']
            print(f"  {'升级开' if allow else '升级关'}+{label:<12}{tag(d['root']):<7}"
                  f"{str(d['min_hp'])+' '+fight:<16}{d['reach']:<10}{d['eq']:<9}"
                  f"{sh[0]*100:3.0f}/{sh[1]*100:3.0f}/{sh[2]*100:3.0f}/{sh[3]*100:3.0f}  "
                  f"[{time.time()-t0:.1f}s]")
