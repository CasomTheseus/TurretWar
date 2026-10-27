#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正 bug 后重跑 v2.0 全部关键实验"""
import time
from collections import defaultdict
import v2_solver as V
from v2_solver import step, WIN, DRAW, LOSS, NAME


def eq_stats(KOMI_S=1, DEADLINE=30, REFLECT=True, REFLECT_DIV=2, H=3):
    """返回根节点结论、均衡路径上的最低基地血、均衡集合大小与行动分布"""
    start, layers, vals = V.solve(H=H, KOMI_S=KOMI_S, DEADLINE=DEADLINE, REFLECT=REFLECT,
                                  REFLECT_DIV=REFLECT_DIV, verbose=False)
    root = vals[0][start]
    eq = [set() for _ in range(DEADLINE + 1)]
    eq[0].add(start)
    for i in range(DEADLINE):
        for st in eq[i]:
            vv = vals[i][st]
            for a in (0, 1, 2):
                kind, payload = step(st, a, DEADLINE, REFLECT, "forces", REFLECT_DIV)
                if kind == 't':
                    continue
                if -vals[i + 1][payload] == vv:
                    eq[i + 1].add(payload)
    hps = [(s[2], s[5]) for i in range(DEADLINE + 1) for s in eq[i]]
    min_hp = min(min(a, b) for a, b in hps) if hps else None
    cnt = defaultdict(int)
    for i in range(DEADLINE):
        for st in eq[i]:
            vv = vals[i][st]
            for a in (0, 1, 2):
                kind, payload = step(st, a, DEADLINE, REFLECT, "forces", REFLECT_DIV)
                if kind == 't':
                    if payload == vv and payload == WIN:
                        cnt[a] += 1
                    continue
                if -vals[i + 1][payload] == vv:
                    cnt[a] += 1
    return dict(root=root, min_hp=min_hp, eq=sum(len(s) for s in eq), cnt=dict(cnt))


def tag(v):
    return {WIN: "先手胜", LOSS: "后手胜", DRAW: "和棋"}[v]


def section(title):
    print()
    print("=" * 112)
    print(title)
    print("=" * 112)


def main():
    section("【1】消融（预算30, H=3）：R2(komi) × R4(反击)")
    for komi in (0, 1, 2):
        for refl in (False, True):
            t0 = time.time()
            d = eq_stats(KOMI_S=komi, DEADLINE=30, REFLECT=refl)
            fight = '有对抗' if (d['min_hp'] and d['min_hp'] < 3) else '无基地伤害'
            print(f"  komi={komi} 反击={'开' if refl else '关'} -> {tag(d['root']):<6} "
                  f"均衡路径最低基地血={d['min_hp']} ({fight}) 均衡集合={d['eq']:<6} "
                  f"均衡上行动分布={d['cnt']} [{time.time()-t0:.1f}s]")

    section("【2】预算扫描（H=3, 反击开）：komi=0 与 komi=1")
    for komi in (0, 1):
        print(f"  --- komi={komi} ---")
        for D in (16, 20, 24, 30):
            d = eq_stats(KOMI_S=komi, DEADLINE=D, REFLECT=True)
            s, l, v = V.solve_scalar(KOMI_S=komi, DEADLINE=D, REFLECT=True)
            sc = v[0][s]
            sc_txt = "完全平衡(0)" if sc == 0 else ("先手可强杀" if sc >= 1_000_000 else "后手可强杀")
            fight = '有对抗' if (d['min_hp'] and d['min_hp'] < 3) else '无基地伤害'
            print(f"    预算{D:<3} 结论={tag(d['root']):<6} 标量={sc:<9} ({sc_txt:<10}) "
                  f"均衡最低基地血={d['min_hp']} {fight}")

    section("【3】退化策略（H=3, 预算30, 反击开, komi=0）")
    for who in (1, 2):
        for a in (0, 1, 2):
            start, layers, vals = V.solve(KOMI_S=0, DEADLINE=30, REFLECT=True,
                                          policy={who: a}, verbose=False)
            print(f"  玩家{who} 永远只「{NAME[a]}」 -> {tag(vals[0][start])}")

    section("【4】反击强度（H=3, 预算30, komi=0）")
    for rd in (0, 6, 4, 3, 2):
        d = eq_stats(KOMI_S=0, DEADLINE=30, REFLECT=(rd > 0), REFLECT_DIV=rd or 2)
        label = '关闭' if rd == 0 else f'每{rd}点反弹1点'
        print(f"  反击={label:<10} -> {tag(d['root']):<6} "
              f"均衡最低基地血={d['min_hp']} 均衡上行动分布={d['cnt']}")


if __name__ == "__main__":
    main()
