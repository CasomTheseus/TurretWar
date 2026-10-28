#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3.0 求解器：不对称阵营（每个玩家有自己的单位参数）。

阵营参数：
  shield : 每次「造护盾」获得的护盾点数（2.0 是 2）
  dmg    : 每座炮台的伤害（2.0 是 1）
  hp     : 初始基地血（2.0 是 3）

其余规则同 2.0：严格轮流、回合预算、超时判分（先比基地血，再比剩余兵力）、护盾反击。

关键用法：
  solveF(f1, f2) 表示玩家1=阵营f1、玩家2=阵营f2。
  因为「先手优势」和「阵营强弱」会混在一起，所以每个对阵都要**交换顺序各测一次**：
    - 两种顺序都由同一阵营获胜 -> 阵营强弱
    - 两种顺序都由先手获胜     -> 节奏优势
自检：两侧都用 standard 时，必须与 v2_solver 完全一致。
"""
import time
from v2_solver import shield_absorb, WIN, DRAW, LOSS

CAPT, CAPS = 8, 16
STANDARD = dict(shield=2, dmg=1, hp=3)


def initF(f1, f2, komi1=0, komi2=0):
    return (0, 1, f1["hp"], 0, komi1, f2["hp"], 0, komi2)


def dvalue(h_m, t_m, s_m, h_o, t_o, s_o):
    if h_m != h_o:
        return WIN if h_m > h_o else LOSS
    f_m, f_o = t_m + s_m, t_o + s_o
    if f_m != f_o:
        return WIN if f_m > f_o else LOSS
    return DRAW


def stepF(st, a, D, f1, f2, REFLECT=True, RN=1, RD=2):
    ply, p, h1, t1, s1, h2, t2, s2 = st
    if p == 1:
        h_m, t_m, s_m = h1, t1, s1
        h_o, t_o, s_o = h2, t2, s2
        f_me = f1
    else:
        h_m, t_m, s_m = h2, t2, s2
        h_o, t_o, s_o = h1, t1, s1
        f_me = f2

    if a == 0:
        t_m = min(t_m + 1, CAPT)
    elif a == 1:
        s_m = min(s_m + f_me["shield"], CAPS)
    else:
        dmg = t_m * f_me["dmg"]
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
        new = (ply + 1, 2, h_m, t_m, s_m, h_o, t_o, s_o)
    else:
        new = (ply + 1, 1, h_o, t_o, s_o, h_m, t_m, s_m)

    if ply + 1 >= D:
        ply2, p2, h1n, t1n, s1n, h2n, t2n, s2n = new
        v = dvalue(h1n, t1n, s1n, h2n, t2n, s2n) if p2 == 1 else \
            dvalue(h2n, t2n, s2n, h1n, t1n, s1n)
        return ('t', -v)
    return ('s', new)


def solveF(f1, f2, D=24, komi1=0, komi2=0, REFLECT=True, RN=1, RD=2, verbose=False):
    start = initF(f1, f2, komi1, komi2)
    layers = [{start}]
    cur = layers[0]
    for _ in range(D):
        nxt = set()
        for st in cur:
            for a in (0, 1, 2):
                kind, payload = stepF(st, a, D, f1, f2, REFLECT, RN, RD)
                if kind == 's':
                    nxt.add(payload)
        layers.append(nxt)
        cur = nxt
    vals = [None] * (D + 1)
    vals[D] = {}
    for st in layers[D]:
        _, p, h1, t1, s1, h2, t2, s2 = st
        vals[D][st] = dvalue(h1, t1, s1, h2, t2, s2) if p == 1 else dvalue(h2, t2, s2, h1, t1, s1)
    for k in range(D - 1, -1, -1):
        v = {}
        for st in layers[k]:
            best = -2
            for a in (0, 1, 2):
                kind, payload = stepF(st, a, D, f1, f2, REFLECT, RN, RD)
                cand = payload if kind == 't' else -vals[k + 1][payload]
                if cand > best:
                    best = cand
            v[st] = best
        vals[k] = v
    if verbose:
        print(f"    [solveF] 可达状态={sum(len(l) for l in layers)}")
    return start, layers, vals


def analyse(f1, f2, D=24, komi1=0, komi2=0, REFLECT=True, RN=1, RD=2):
    start, layers, vals = solveF(f1, f2, D, komi1, komi2, REFLECT, RN, RD)
    root = vals[0][start]
    eq = [set() for _ in range(D + 1)]
    eq[0].add(start)
    for i in range(D):
        for st in eq[i]:
            vv = vals[i][st]
            for a in (0, 1, 2):
                kind, payload = stepF(st, a, D, f1, f2, REFLECT, RN, RD)
                if kind != 's':
                    continue
                if -vals[i + 1][payload] == vv:
                    eq[i + 1].add(payload)
    hps = [min(s[2], s[5]) for i in range(D + 1) for s in eq[i]]
    hp0 = min(f1["hp"], f2["hp"])
    return dict(root=root, min_hp=min(hps) if hps else None, hp0=hp0,
                eq=sum(len(s) for s in eq), reach=sum(len(l) for l in layers))


def tag(v, f1, f2):
    if v == DRAW:
        return "和棋"
    return "玩家1(先手/{}）胜".format(f1["name"]) if v == WIN else "玩家2(后手/{}）胜".format(f2["name"])


def mk(name, shield, dmg, hp=3):
    return dict(name=name, shield=shield, dmg=dmg, hp=hp)


if __name__ == "__main__":
    import v2_solver as V
    print("=" * 116)
    print("自检：两侧都用 standard 时，必须与 v2_solver 一致")
    print("=" * 116)
    for D, komi, refl, rn, rd in ((16, 0, True, 1, 2), (16, 1, False, 1, 2), (20, 0, True, 1, 3)):
        _, _, vF = solveF(STANDARD, STANDARD, D, komi, 0, refl, rn, rd)
        s, l, v2 = V.solve(KOMI_S=komi, DEADLINE=D, REFLECT=refl, RN=rn, REFLECT_DIV=rd, verbose=False)
        a = vF[0][initF(STANDARD, STANDARD, komi, 0)]
        b = v2[0][s]
        print(f"  D={D:<3} komi={komi} 反击={'开' if refl else '关'}: solveF={a:+d}  v2={b:+d}  {'OK' if a == b else '***不一致***'}")

    print()
    print("=" * 116)
    print("阵营对阵扫描（预算24, komi=0, 反击1/2）：每个对阵交换顺序各测一次")
    print("=" * 116)
    std = mk("标准", 2, 1)
    bul = mk("壁垒(盾3)", 3, 1)
    stk = mk("突击(伤2)", 2, 2)
    print(f"  {'玩家1阵营':<12}{'玩家2阵营':<12}{'结论':<20}{'均衡最低基地血':<18}{'均衡集合':<9}")
    pairs = [(std, std), (bul, stk), (stk, bul), (bul, std), (std, bul), (stk, std), (std, stk)]
    for f1, f2 in pairs:
        t0 = time.time()
        d = analyse(f1, f2)
        combat = "有对抗" if (d["min_hp"] is not None and d["min_hp"] < d["hp0"]) else "零基地伤害"
        print(f"  {f1['name']:<12}{f2['name']:<12}{tag(d['root'], f1, f2):<20}"
              f"{str(d['min_hp'])+' '+combat:<18}{d['eq']:<9}[{time.time()-t0:.1f}s]")
