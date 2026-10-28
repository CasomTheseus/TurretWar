/* ============================================================
 * TurretWar 3.0  —— "炮台战争"（不对称阵营）
 *
 * 3.0 相对 2.0 的唯一改动：把「双方完全对称」改成「两个阵营不对称」。
 * 求解器结论：对称规则下平衡只能靠僵持实现；一旦引入阵营差，对局立刻
 * 变回真实的攻防（基地血会被打掉、出现胜负），代价是完美对弈下必有胜负。
 *
 * 阵营（其余规则全部同 2.0）：
 *   壁垒：造护盾 +3，炮台伤害 1，开局护盾 0
 *   突击：造护盾 +2，炮台伤害 2，开局护盾 1   <- 1 点护盾是标定出的补偿
 *
 * 平衡标定（求解器实测，预算 24 手、反击 1/2）：
 *   不给补偿       -> 壁垒在两种先手分配下都赢（壁垒偏强）
 *   突击 +1 护盾   -> 两种分配都由「先手方」获胜（两侧强度相当，胜负回到节奏）
 *   突击 +3 护盾   -> 突击反过来两种都赢
 * 因此 3.0 采用「突击 +1 护盾」。完美对弈下先手方必胜，单局胜负取决于
 * 谁能抓住对方的失误；正式比赛建议双局换边（见 RULES-3.0.md）。
 *
 * 其余 2.0 规则不变：
 *   R1 严格轮流（玩家1先手）
 *   R2 后手补偿：见上方阵营标定（不再有额外的对称 komi）
 *   R3 回合预算 24 手，到期比 基地血 -> 剩余兵力(炮台+护盾) -> 和棋
 *   R4 护盾反击：被护盾吸收 k 点 -> 攻击方受 k/2 点（击杀优先，不再递归）
 *
 * 编码：UTF-8（无 BOM）。MSVC 编译请加 /utf-8。
 * 编译：clang -x c -std=c11 -Wall -Wextra -o turretwar3 TurretWar.AlphaTest_3.0.cpp
 * 调试：-DINTRO_DELAY=0 关闭开场等待
 * ============================================================ */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define BASE_HEALTH   3
#define TURN_BUDGET   24
#define REFLECT_DIV   2

#ifndef INTRO_DELAY
#define INTRO_DELAY 1
#endif

/* ---------- 阵营 ---------- */

typedef struct {
    const char *name;
    int shieldGain;     /* 每次造护盾获得点数 */
    int turretDamage;   /* 每座炮台伤害 */
    int startShield;    /* 开局护盾（标定补偿） */
    const char *desc;
} Faction;

#define FACTION_COUNT 2

static const Faction FACTIONS[FACTION_COUNT] = {
    { "壁垒", 3, 1, 0, "造护盾+3，炮台伤害1，开局护盾0" },
    { "突击", 2, 2, 1, "造护盾+2，炮台伤害2，开局护盾1" },
};

/* ---------- 玩家 ---------- */

typedef struct {
    int baseHealth;
    int turretCount;
    int shieldCount;
    int faction;              /* 阵营下标 */
    int totalShieldsBuilt;
    int totalTurretsBuilt;
    int totalDamageDealt;
} Player;

static const Faction *factionOf(const Player *p) {
    return &FACTIONS[p->faction];
}

/* ---------- 显示 ---------- */

void printStatus(Player *player, int playerNumber) {
    printf("玩家%d[%s]状态：基地生命值：%d，炮台数量：%d，护盾数量：%d\n",
           playerNumber, factionOf(player)->name,
           player->baseHealth, player->turretCount, player->shieldCount);
}

void printFactionInfo(const Player *player, int playerNumber) {
    const Faction *f = factionOf(player);
    printf("玩家%d 阵营：%s（%s）\n", playerNumber, f->name, f->desc);
}

/* ---------- 建造（按阵营取值） ---------- */

void buildTurret(Player *player) {
    player->turretCount++;
    player->totalTurretsBuilt++;
}

void buildShield(Player *player) {
    int gain = factionOf(player)->shieldGain;
    player->shieldCount += gain;
    player->totalShieldsBuilt += gain;
}

/* 把 damage 点伤害结算给 p：护盾 -> 炮台 -> 基地。返回被护盾吸收的点数 */
int applyDamage(int damage, Player *p) {
    int absorbed = 0;
    while (damage > 0 && p->baseHealth > 0) {
        if (p->shieldCount > 0) {
            p->shieldCount--;
            absorbed++;
        } else if (p->turretCount > 0) {
            p->turretCount--;
        } else {
            p->baseHealth--;
        }
        damage--;
    }
    return absorbed;
}

static int materialLoss(int s0, int t0, int h0, Player *p) {
    return (s0 - p->shieldCount) + (t0 - p->turretCount) + (h0 - p->baseHealth);
}

/* ---------- 进攻 + 护盾反击（伤害按阵营倍率） ---------- */

void attack(Player *attacker, Player *defender) {
    int damage = attacker->turretCount * factionOf(attacker)->turretDamage;
    int s0 = defender->shieldCount, t0 = defender->turretCount, h0 = defender->baseHealth;

    int absorbed = applyDamage(damage, defender);
    attacker->totalDamageDealt += materialLoss(s0, t0, h0, defender);

    /* 击杀优先：本次进攻已击毁对方基地，则不结算反弹 */
    if (defender->baseHealth <= 0) return;

    /* 反弹量 <= 吸收量 <= 攻方炮台数，必然先被攻方自己的炮台吃掉，打不到攻方基地。
       下面的基地检查因此不可达，仅作防御性保留。 */
    int reflect = absorbed / REFLECT_DIV;
    if (reflect > 0) {
        int as0 = attacker->shieldCount, at0 = attacker->turretCount, ah0 = attacker->baseHealth;
        applyDamage(reflect, attacker);
        defender->totalDamageDealt += materialLoss(as0, at0, ah0, attacker);
    }
}

/* ---------- 超时判分 ---------- */

int judgeByDeadline(Player *player1, Player *player2) {
    if (player1->baseHealth != player2->baseHealth) {
        return player1->baseHealth > player2->baseHealth ? 1 : 2;
    }
    int force1 = player1->turretCount + player1->shieldCount;
    int force2 = player2->turretCount + player2->shieldCount;
    if (force1 != force2) {
        return force1 > force2 ? 1 : 2;
    }
    return 0;
}

/* ---------- 结算与信息 ---------- */

void printGameSummary(Player *player1, Player *player2) {
    printf("\n===== 游戏结算 =====\n");
    printf("玩家1[%s] 累计建造护盾量：%d\n", factionOf(player1)->name, player1->totalShieldsBuilt);
    printf("玩家1[%s] 累计建造炮台量：%d\n", factionOf(player1)->name, player1->totalTurretsBuilt);
    printf("玩家1[%s] 累计造成伤害量（实际命中，不含溢出炮弹）：%d\n",
           factionOf(player1)->name, player1->totalDamageDealt);
    printf("玩家1[%s] 剩余兵力：%d（炮台%d + 护盾%d）\n", factionOf(player1)->name,
           player1->turretCount + player1->shieldCount,
           player1->turretCount, player1->shieldCount);
    printf("------------------------\n");
    printf("玩家2[%s] 累计建造护盾量：%d\n", factionOf(player2)->name, player2->totalShieldsBuilt);
    printf("玩家2[%s] 累计建造炮台量：%d\n", factionOf(player2)->name, player2->totalTurretsBuilt);
    printf("玩家2[%s] 累计造成伤害量（实际命中，不含溢出炮弹）：%d\n",
           factionOf(player2)->name, player2->totalDamageDealt);
    printf("玩家2[%s] 剩余兵力：%d（炮台%d + 护盾%d）\n", factionOf(player2)->name,
           player2->turretCount + player2->shieldCount,
           player2->turretCount, player2->shieldCount);
    printf("====================\n");
    sleep(INTRO_DELAY ? 2 : 0);
}

void printAuthorInfo(void) {
    printf("\n==========游戏信息==========\n");
    printf("Gamename:TurretWar,炮台战争\n");
    printf("GameVersion:AlphaTest_3.0\n");
    printf("\n==========作者信息==========\n");
    printf("GameDeveloper:QuanYuhang XuDalin JiangHaoyu RenXinduo WangKewei Wangruiqi\n");
    printf("Game Inspiration Proposer：QuanYuhang\n");
    printf("Code By:Casom Theseus\n");
    printf("Thanks for your playing!\n");
    printf("==========END==========\n");
}

void printRules(void) {
    static const char *rules =
        "游戏规则说明（3.0）：\n\n"
        "欢迎来到炮台战争！3.0 引入了两个不对称阵营。\n\n"
        "1. 阵营（开局由玩家1选择，玩家2使用另一个）：\n"
        "   - 壁垒：每次造护盾 +3，每座炮台伤害 1，开局护盾 0。\n"
        "   - 突击：每次造护盾 +2，每座炮台伤害 2，开局护盾 1（平衡补偿）。\n\n"
        "2. 初始设置：\n"
        "   - 双方基地生命值均为3，且无法补充。\n"
        "   - 炮台数量初始为0；护盾数量见阵营开局值。\n\n"
        "3. 玩家行动：\n"
        "   - 玩家1先手，双方严格轮流行动。\n"
        "   - 每次从三种操作中选一种：造炮台(+1) / 造护盾(按阵营) / 发起进攻。\n\n"
        "4. 伤害计算：\n"
        "   - 伤害 = 炮台数 × 阵营伤害（壁垒1、突击2）。\n"
        "   - 结算顺序：护盾 -> 炮台 -> 基地。\n\n"
        "5. 护盾反击：\n"
        "   - 一次进攻中被护盾吸收的每2点伤害，反弹1点给进攻方，\n"
        "     同样按 护盾->炮台->基地 结算（实际会先消耗攻方自己的炮台）。\n"
        "   - 若这次进攻已击毁对方基地，则不再结算反弹；反弹不再触发反击。\n\n"
        "6. 回合预算与胜负判定：\n"
        "   - 双方合计最多24手；任何一方基地归零，对方立即获胜。\n"
        "   - 24手用完双方都还活着时，依次比较：\n"
        "     ① 基地生命值；② 剩余兵力（炮台+护盾）；③ 仍相同判和棋。\n\n"
        "提示：求解器显示在完美对弈下先手方占优，单局胜负主要看谁先失误；\n"
        "正式比赛建议双局换边（双方各用一次两个阵营），再以用到的回合数分胜负。\n\n"
        "祝你游戏愉快！\n";
    printf("%s", rules);
}

/* ---------- 输入 ---------- */

int readChoice(const char *prompt, int lo, int hi, int *out) {
    char line[128];
    for (;;) {
        printf("%s", prompt);
        fflush(stdout);
        if (fgets(line, sizeof line, stdin) == NULL) {
            return 0;
        }
        if (strchr(line, '\n') == NULL) {
            int c;
            while ((c = getchar()) != '\n' && c != EOF) { }
        }
        char *end;
        long value = strtol(line, &end, 10);
        if (end != line) {
            char *rest = end;
            while (*rest == ' ' || *rest == '\t' || *rest == '\r' || *rest == '\n') rest++;
            if (*rest == '\0' && value >= lo && value <= hi) {
                *out = (int)value;
                return 1;
            }
        }
        printf("无效的选择，请重新输入。\n");
    }
}

/* ---------- 阵营选择 ---------- */

/* 玩家1 选阵营；返回 0=输入结束 */
static int chooseFactions(int *f1, int *f2) {
    printf("\n请选择阵营：\n");
    for (int i = 0; i < FACTION_COUNT; i++) {
        printf("  %d. %s（%s）\n", i + 1, FACTIONS[i].name, FACTIONS[i].desc);
    }
    int pick;
    if (!readChoice("玩家1 请选择阵营：", 1, FACTION_COUNT, &pick)) {
        return 0;
    }
    *f1 = pick - 1;
    *f2 = (*f1 == 0) ? 1 : 0;
    printf("玩家1 选了 %s，玩家2 使用 %s。\n",
           FACTIONS[*f1].name, FACTIONS[*f2].name);
    return 1;
}

/* ---------- 一局游戏 ---------- */

int playGame(int showRules) {
    if (showRules) {
        printRules();
    }

    int f1 = 0, f2 = 1;
    if (!chooseFactions(&f1, &f2)) {
        printf("\n输入已结束，程序退出。\n");
        return 0;
    }

    Player player1 = { BASE_HEALTH, 0, FACTIONS[f1].startShield, f1, 0, 0, 0 };
    Player player2 = { BASE_HEALTH, 0, FACTIONS[f2].startShield, f2, 0, 0, 0 };

    printFactionInfo(&player1, 1);
    printFactionInfo(&player2, 2);

    printf("欢迎来到炮台战争！\n");
    fflush(stdout);
    sleep(INTRO_DELAY ? 2 : 0);
    printf("敌军还有五秒到达战场，请做好准备！\n");
    fflush(stdout);
    sleep(INTRO_DELAY ? 5 : 0);
    printf("全军出击！\n");
    fflush(stdout);
    sleep(INTRO_DELAY ? 2 : 0);

    for (int ply = 1; ply <= TURN_BUDGET; ply++) {
        int currentPlayerNumber = (ply % 2 == 1) ? 1 : 2;
        Player *currentAttacker = (currentPlayerNumber == 1) ? &player1 : &player2;
        Player *currentDefender = (currentPlayerNumber == 1) ? &player2 : &player1;

        printf("\n【第 %d/%d 手】\n", ply, TURN_BUDGET);
        printStatus(currentAttacker, currentPlayerNumber);
        printStatus(currentDefender, currentPlayerNumber == 1 ? 2 : 1);
        printf("玩家%d的回合，请选择行动：\n", currentPlayerNumber);
        printf("1. 建造炮台;\n");
        printf("2. 建造护盾;\n");
        printf("3. 发起进攻;\n");

        char prompt[80];
        snprintf(prompt, sizeof prompt, "请做出玩家%d的选择：", currentPlayerNumber);
        int choice;
        if (!readChoice(prompt, 1, 3, &choice)) {
            printf("\n输入已结束，程序退出。\n");
            return 0;
        }

        switch (choice) {
            case 1: buildTurret(currentAttacker); break;
            case 2: buildShield(currentAttacker); break;
            case 3: attack(currentAttacker, currentDefender); break;
        }

        if (currentDefender->baseHealth <= 0) {
            printf("玩家%d[%s]获胜！（击毁敌方基地）\n",
                   currentPlayerNumber, factionOf(currentAttacker)->name);
            printGameSummary(&player1, &player2);
            return 1;
        }
        if (currentAttacker->baseHealth <= 0) {
            printf("玩家%d[%s]获胜！（护盾反击击毁进攻方基地）\n",
                   currentPlayerNumber == 1 ? 2 : 1, factionOf(currentDefender)->name);
            printGameSummary(&player1, &player2);
            return 1;
        }
    }

    printf("\n===== %d 手预算用完，进入超时判分 =====\n", TURN_BUDGET);
    printStatus(&player1, 1);
    printStatus(&player2, 2);
    int winner = judgeByDeadline(&player1, &player2);
    if (winner == 0) {
        printf("双方基地生命值与剩余兵力均相同 —— 判和棋。\n");
    } else {
        printf("玩家%d[%s]获胜！（超时判分：基地血 %d:%d，剩余兵力 %d:%d）\n",
               winner,
               winner == 1 ? factionOf(&player1)->name : factionOf(&player2)->name,
               player1.baseHealth, player2.baseHealth,
               player1.turretCount + player1.shieldCount,
               player2.turretCount + player2.shieldCount);
    }
    printGameSummary(&player1, &player2);
    return 1;
}

int main(void) {
    int firstGame = 1;

    for (;;) {
        if (!playGame(firstGame)) {
            break;
        }
        firstGame = 0;

        printf("\n是否再战？\n");
        printf("1. 再战\n");
        printf("0. 退出\n");

        int again;
        if (!readChoice("请选择：", 0, 1, &again)) {
            printf("\n输入已结束，程序退出。\n");
            break;
        }
        if (again != 1) {
            printAuthorInfo();
            break;
        }
    }

    return 0;
}
