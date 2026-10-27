#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TurretWar v2.0 求解器（精确解）

规则（与 2.0 更新内容一一对应）：
  R1 严格轮流，玩家1先手
  R2 后手补偿：玩家2 开局护盾 KOMI_S（默认 1）
  R3 回合预算 DEADLINE 手：到期比 ①基地血 ②剩余兵力(炮台+护盾) ③和棋
  R4 护盾反击：本次被护盾吸收 k 点 -> 攻击方受 k//2 点，按 护盾->炮台->基地 结算；
     反弹不再反击；若本次进攻已击毁对方基地则不结算反弹

实现要点：R3 使 ply 严格递增 -> 博弈图是无环的
  => 用"逐层回溯 DP"（前向可达集 + 后向归纳），比带环博弈的吸引子算法更快且无歧义。
状态： (ply, p, h1,t1,s1,h2,t2,s2)
"""
import sys, time, json
from collections import defaultdict

WIN, DRAW, LOSS = 1, 0, -1
NAME = {0: "造炮台", 1: "造护盾", 2: "进攻"}
CAPT, CAPS = 8, 16          # 炮台/护盾上限（脚本会自检是否绑定）


def shield_absorb(dmg, s, t, h):
    """逐点结算，返回 (剩余dmg, s, t, h, 被护盾吸收数)"""
    absorbed = 0
    while dmg > 0 and h > 0:
        if s > 0:
            s -= 1; absorbed += 1
        elif t > 0:
            t -= 1
        else:
            h -= 1
        dmg -= 1
    return dmg, s, t, h, absorbed


def absorb_no_base(dmg, s, t):
    """只吃掉护盾和炮台，剩余伤害丢弃（用于"反伤不伤基地"变体）"""
    while dmg > 0 and (s > 0 or t > 0):
        if s > 0: s -= 1
        elif t > 0: t -= 1
        dmg -= 1
    return s, t


def init_state(H, KOMI_S, KOMI_T=0):
    return (0, 1, H, 0, 0, H, KOMI_T, KOMI_S)


def deadline_value(h_me, t_me, s_me, h_op, t_op, s_op, tie="forces"):
    """到期判分，返回当前行动者视角的胜负"""
    if h_me != h_op:
        return WIN if h_me > h_op else LOSS
    if tie == "forces":
        f_me, f_op = t_me + s_me, t_op + s_op
        if f_me != f_op:
            return WIN if f_me > f_op else LOSS
    return DRAW


def step(st, a, DEADLINE, REFLECT=True, TIE="forces", REFLECT_DIV=2, RN=1, RD=None, REFLECT_NO_BASE=False, DECAY=0):
    """返回 ('t', 值) 终局，或 ('s', 新状态)。值以"当前行动者"视角"""
    ply, p, h1, t1, s1, h2, t2, s2 = st
    if p == 1:
        me, op = (h1, t1, s1), (h2, t2, s2)
    else:
        me, op = (h2, t2, s2), (h1, t1, s1)
    h_m, t_m, s_m = me
    h_o, t_o, s_o = op
    if DECAY:                       # 护盾衰减：每回合开始时，行动方自身护盾 -DECAY（不低于 0）
        s_m = max(0, s_m - DECAY)
    if a == 0:
        t_m = min(t_m + 1, CAPT)
    elif a == 1:
        s_m = min(s_m + 2, CAPS)
    else:
        if t_m > 0 and h_o > 0:
            _, s_o, t_o, h_o, absorbed = shield_absorb(t_m, s_o, t_o, h_o)
            if h_o <= 0:
                return ('t', WIN)                      # 击杀优先，不结算反弹
            if REFLECT and REFLECT_DIV > 0:
                _rd = RD if RD else REFLECT_DIV
                refl = (absorbed * RN) // _rd   # 反伤比例 = RN/RD
                if refl > 0:
                    if REFLECT_NO_BASE:
                        s_m, t_m = absorb_no_base(refl, s_m, t_m)
                    else:
                        _, s_m, t_m, h_m, _ = shield_absorb(refl, s_m, t_m, h_m)
                        if h_m <= 0:
                            return ('t', LOSS)         # 被反杀
    if p == 1:
        new = (ply + 1, 2, h_m, t_m, s_m, h_o, t_o, s_o)
    else:
        new = (ply + 1, 1, h_o, t_o, s_o, h_m, t_m, s_m)
    if ply + 1 >= DEADLINE:
        ply2, p2, h1n, t1n, s1n, h2n, t2n, s2n = new
        # 终止值约定：站在"刚刚行动的一方"视角（与击杀终局一致）
        # new 里 p 已经换成对手，所以先算对手视角再取负
        if p2 == 1:
            v_next = deadline_value(h1n, t1n, s1n, h2n, t2n, s2n, TIE)
        else:
            v_next = deadline_value(h2n, t2n, s2n, h1n, t1n, s1n, TIE)
        return ('t', -v_next)
    return ('s', new)


def scalar_terminal(st, TIE="forces"):
    """和棋博弈的细粒度收益：主判据(胜/和/负) -> 基地血差 -> 兵力差。用于标定 komi。"""
    ply, p, h1, t1, s1, h2, t2, s2 = st
    if p == 1:
        hm, tm, sm, ho, to, so = h1, t1, s1, h2, t2, s2
    else:
        hm, tm, sm, ho, to, so = h2, t2, s2, h1, t1, s1
    dh = hm - ho
    df = (tm + sm) - (to + so)
    if dh != 0:
        sign = 1 if dh > 0 else -1
    elif df != 0:
        sign = 1 if df > 0 else -1
    else:
        sign = 0
    return 1_000_000 * sign + 1_000 * dh + df


def solve_scalar(H=3, KOMI_S=1, DEADLINE=30, REFLECT=True, TIE="forces", REFLECT_DIV=2, verbose=False, RN=1, REFLECT_NO_BASE=False, DECAY=0):
    """同 solve，但终局用标量收益（可比较"和棋偏向谁"、"赢多少"）"""
    start = init_state(H, KOMI_S)
    layers = [{start}]; cur = layers[0]
    for k in range(DEADLINE):
        nxt = set()
        for st in cur:
            for a in (0, 1, 2):
                kind, payload = step(st, a, DEADLINE, REFLECT, TIE, REFLECT_DIV, RN, REFLECT_DIV, REFLECT_NO_BASE, DECAY)
                if kind == 's':
                    nxt.add(payload)
        layers.append(nxt); cur = nxt
    vals = [None] * (DEADLINE + 1)
    vals[DEADLINE] = {st: -scalar_terminal(st, TIE) for st in layers[DEADLINE]}
    for k in range(DEADLINE - 1, -1, -1):
        v = {}
        for st in layers[k]:
            best = None
            for a in (0, 1, 2):
                kind, payload = step(st, a, DEADLINE, REFLECT, TIE, REFLECT_DIV, RN, REFLECT_DIV, REFLECT_NO_BASE, DECAY)
                if kind == 't':
                    cand = 1_000_000 * payload
                else:
                    cand = -vals[k + 1][payload]
                if best is None or cand > best: best = cand
            v[st] = best
        vals[k] = v
    if verbose:
        print(f"    [标量求解] 状态总数={sum(len(l) for l in layers)}")
    return start, layers, vals


def solve(H=3, KOMI_S=1, DEADLINE=30, REFLECT=True, TIE="forces", policy=None, verbose=True, REFLECT_DIV=2, RN=1, REFLECT_NO_BASE=False, DECAY=0):
    """policy: {1: 强制行动 or None, 2: ...} 用于检验退化策略"""
    policy = policy or {}
    start = init_state(H, KOMI_S)
    layers = [ {start} ]
    cur = layers[0]
    for k in range(DEADLINE):
        nxt = set()
        for st in cur:
            p = st[1]
            acts = [policy[p]] if policy.get(p) is not None else (0, 1, 2)
            for a in acts:
                kind, payload = step(st, a, DEADLINE, REFLECT, TIE, REFLECT_DIV, RN, REFLECT_DIV, REFLECT_NO_BASE, DECAY)
                if kind == 's':
                    nxt.add(payload)
        layers.append(nxt)
        cur = nxt
    # 到期层终局值
    vals = [None] * (DEADLINE + 1)
    vals[DEADLINE] = {st: deadline_value(st[2], st[3], st[4], st[5], st[6], st[7], TIE)
                      if st[1] == 1 else deadline_value(st[5], st[6], st[7], st[2], st[3], st[4], TIE)
                      for st in layers[DEADLINE]}
    for k in range(DEADLINE - 1, -1, -1):
        v = {}
        for st in layers[k]:
            p = st[1]
            acts = [policy[p]] if policy.get(p) is not None else (0, 1, 2)
            best = -2
            for a in acts:
                kind, payload = step(st, a, DEADLINE, REFLECT, TIE, REFLECT_DIV, RN, REFLECT_DIV, REFLECT_NO_BASE, DECAY)
                if kind == 't':
                    cand = payload
                else:
                    cand = -vals[k + 1][payload]
                if cand > best: best = cand
            v[st] = best
        vals[k] = v
    if verbose:
        tot = sum(len(l) for l in layers)
        print(f"    [求解] 层数={DEADLINE+1} 可达状态总数={tot} 最大单层={max(len(l) for l in layers)}")
    return start, layers, vals


if __name__ == "__main__":
    print("=" * 70)
    print("第一步：先看预算是否真的起作用（R1+R2 但不同预算）")
    print("=" * 70)
    for d in (20, 25, 30, 40, 60):
        report(f"预算 {d} 手 | komi护盾1 | 有反击", H=3, KOMI_S=1, DEADLINE=d, REFLECT=True)
