/* ============================================================
 * TurretWar 2.0  —— "炮台战争"
 *
 * 2.0 规则（对应 README 的 AlphaTest_2.0 更新内容）：
 *   R1 严格轮流行动：玩家1先手，双方交替，不再随机选人
 *   R2 无后手补偿：双方基地血 3、炮台 0、护盾 0
 *   R3 回合预算 24 手：到期若双方基地血均 > 0，先比基地血，
 *      再比剩余兵力(炮台数+护盾数)，仍相同判和棋
 *   R4 护盾反击：一次进攻中被护盾吸收 k 点，攻击方受 k/2 点，
 *      按"护盾→炮台→基地"结算；击杀优先，反弹不再触发反击
 *
 * 参数依据（离线求解器对 1.0/2.0 规则的精确求解）：
 *   - 后手补偿取 0：给后手 1 点护盾会让后手反过来能强杀，补偿过头；
 *   - 预算取 24 手：16 手时决策偏向堆护盾，24 手起"进攻时机"成为主要决策；
 *   - 反击取每 2 点 1 点：反击率 >= 1/3 才能消除"先手必胜"，1/2 的均衡多样性最好。
 *
 * 编码：UTF-8（无 BOM）。Windows 上用 MSVC 编译请加 /utf-8，
 *       否则中文会按系统 ANSI 代码页解释而出现乱码。
 * 编译：clang -x c -std=c11 -Wall -Wextra -o turretwar2 TurretWar.AlphaTest_2.0.cpp
 *       或 g++ TurretWar.AlphaTest_2.0.cpp -o turretwar2   (本文件同时是合法 C++)
 * 调试：-DINTRO_DELAY=0 可关闭开场动画的等待
 * ============================================================ */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
/* 2.0 已移除随机行动，故不再需要 <time.h> 与 srand() */

#define BASE_HEALTH   3    /* 基地血（不可恢复） */
#define TURN_BUDGET   24   /* R3 回合预算（双方合计手数） */
#define REFLECT_DIV   2    /* R4 每 2 点被护盾吸收 -> 反弹 1 点 */

#ifndef INTRO_DELAY
#define INTRO_DELAY 1      /* 开场动画等待（秒级），测试时用 -DINTRO_DELAY=0 关闭 */
#endif

typedef struct {
    int baseHealth;
    int turretCount;
    int shieldCount;
    int totalShieldsBuilt;
    int totalTurretsBuilt;
    int totalDamageDealt;
} Player;

/* ---------- 显示 ---------- */

void printStatus(Player *player, int playerNumber) {
    printf("玩家%d状态：基地生命值：%d，炮台数量：%d，护盾数量：%d\n",
           playerNumber, player->baseHealth, player->turretCount, player->shieldCount);
}

/* ---------- 建造 ---------- */

void buildTurret(Player *player) {
    player->turretCount++;
    player->totalTurretsBuilt++;
}

void buildShield(Player *player) {
    player->shieldCount += 2;
    player->totalShieldsBuilt += 2;
}

/* 把 damage 点伤害结算给 p：护盾 -> 炮台 -> 基地。
   返回"被护盾吸收的点数"，用于 R4 的反弹计算。 */
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

/* 用"结算前后材料差"统计实际造成的伤害（不含溢出浪费的炮弹） */
static int materialLoss(int s0, int t0, int h0, Player *p) {
    return (s0 - p->shieldCount) + (t0 - p->turretCount) + (h0 - p->baseHealth);
}

/* ---------- R4：进攻 + 护盾反击 ---------- */

void attack(Player *attacker, Player *defender) {
    int s0 = defender->shieldCount, t0 = defender->turretCount, h0 = defender->baseHealth;

    int absorbed = applyDamage(attacker->turretCount, defender);
    attacker->totalDamageDealt += materialLoss(s0, t0, h0, defender);

    /* 击杀优先：本次进攻已击毁对方基地，则不结算反弹 */
    if (defender->baseHealth <= 0) return;

    /* 反弹量 = floor(被护盾吸收 / REFLECT_DIV)。
       注意：反弹量 <= 吸收量 <= 攻方炮台数，而反弹按 护盾->炮台->基地 结算，
       所以它必然先被攻方自己的炮台吃掉，**打不到攻方基地**。
       下面的基地检查因此在本规则下不可达，仅作为防御性判断保留。 */
    int reflect = absorbed / REFLECT_DIV;
    if (reflect > 0) {
        int as0 = attacker->shieldCount, at0 = attacker->turretCount, ah0 = attacker->baseHealth;
        applyDamage(reflect, attacker);
        defender->totalDamageDealt += materialLoss(as0, at0, ah0, attacker);
    }
}

/* ---------- R3：超时判分 ---------- */

/* 返回 1=玩家1胜, 2=玩家2胜, 0=和棋 */
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
    printf("玩家1累计建造护盾量：%d\n", player1->totalShieldsBuilt);
    printf("玩家1累计建造炮台量：%d\n", player1->totalTurretsBuilt);
    printf("玩家1累计造成伤害量：%d\n", player1->totalDamageDealt);
    printf("玩家1剩余兵力：%d（炮台%d + 护盾%d）\n",
           player1->turretCount + player1->shieldCount, player1->turretCount, player1->shieldCount);
    printf("------------------------\n");
    printf("玩家2累计建造护盾量：%d\n", player2->totalShieldsBuilt);
    printf("玩家2累计建造炮台量：%d\n", player2->totalTurretsBuilt);
    printf("玩家2累计造成伤害量：%d\n", player2->totalDamageDealt);
    printf("玩家2剩余兵力：%d（炮台%d + 护盾%d）\n",
           player2->turretCount + player2->shieldCount, player2->turretCount, player2->shieldCount);
    printf("====================\n");
    sleep(INTRO_DELAY ? 2 : 0);
}

void printAuthorInfo(void) {
    printf("\n==========游戏信息==========\n");
    printf("Gamename:TurretWar,炮台战争\n");
    printf("GameVersion:AlphaTest_2.0\n");
    printf("\n==========作者信息==========\n");
    printf("GameDeveloper:QuanYuhang XuDalin JiangHaoyu RenXinduo WangKewei Wangruiqi\n");
    printf("Game Inspiration Proposer：QuanYuhang\n");
    printf("Code By:Casom Theseus\n");
    printf("Thanks for your playing!\n");
    printf("==========END==========\n");
}

void printRules(void) {
    static const char *rules =
        "游戏规则说明（2.0）：\n\n"
        "欢迎来到炮台战争！以下是游戏的基本规则：\n\n"
        "1. 初始设置：\n"
        "   - 每位玩家的基地生命值初始为3，且无法补充。\n"
        "   - 炮台数量和护盾数量初始均为0。\n\n"
        "2. 玩家行动：\n"
        "   - 玩家1先手，双方严格轮流行动（不再随机选人）。\n"
        "   - 行动时，玩家可以选择以下三种操作之一：\n"
        "     - 建造炮台：增加1个炮台。\n"
        "     - 建造护盾：增加2个护盾。\n"
        "     - 发起进攻：使用所有炮台对敌方进行攻击，每个炮台发射一枚炮弹。\n\n"
        "3. 伤害计算：\n"
        "   - 当造成伤害时，首先减少敌方的护盾数量。\n"
        "   - 如果护盾归零，继续攻击敌方的炮台。\n"
        "   - 如果炮台也归零，最后攻击敌方的基地。\n\n"
        "4. 护盾反击：\n"
        "   - 一次进攻中被护盾吸收的每2点伤害，会反弹1点给进攻方，\n"
        "     同样按 护盾->炮台->基地 的顺序结算（实际会先消耗攻方自己的炮台）。\n"
        "   - 若这次进攻已经击毁对方基地，则不再结算反弹（击杀优先）。\n"
        "   - 反弹不会再次触发反击。\n\n"
        "5. 回合预算与胜负判定：\n"
        "   - 双方合计最多24手；任何一方基地生命值归零，对方立即获胜。\n"
        "   - 24手用完双方都还活着时，依次比较：\n"
        "     ① 基地生命值多者胜；\n"
        "     ② 相同则比较剩余兵力（炮台数+护盾数），多者胜；\n"
        "     ③ 仍相同则判和棋。\n\n"
        "请确保在行动时立即执行选择的操作，无法存储行动。\n\n"
        "祝你游戏愉快！\n";
    printf("%s", rules);
}

/* ---------- 输入：读整行再解析 ---------- */

/* 读取 lo..hi 之间的整数。返回 1=成功，0=输入结束(EOF)，调用者应退出程序。
   解析失败或越界时重问，不会把坏字符留在缓冲区里造成死循环。 */
int readChoice(const char *prompt, int lo, int hi, int *out) {
    char line[128];
    for (;;) {
        printf("%s", prompt);
        fflush(stdout);
        if (fgets(line, sizeof line, stdin) == NULL) {
            return 0;
        }
        if (strchr(line, '\n') == NULL) {          /* 超长行：丢弃剩余部分 */
            int c;
            while ((c = getchar()) != '\n' && c != EOF) { }
        }
        char *end;
        long value = strtol(line, &end, 10);
        if (end != line) {                          /* 至少解析出一个整数 */
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

/* ---------- 一局游戏 ---------- */

/* 返回 1=本局结束，0=输入结束（应退出程序） */
int playGame(int showRules) {
    Player player1 = {BASE_HEALTH, 0, 0, 0, 0, 0};
    Player player2 = {BASE_HEALTH, 0, 0, 0, 0, 0};

    if (showRules) {
        printRules();
    }

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
        int currentPlayerNumber = (ply % 2 == 1) ? 1 : 2;   /* R1 严格轮流 */
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
            printf("玩家%d获胜！（击毁敌方基地）\n", currentPlayerNumber);
            printGameSummary(&player1, &player2);
            return 1;
        }
        if (currentAttacker->baseHealth <= 0) {
            printf("玩家%d获胜！（护盾反击击毁进攻方基地）\n", currentPlayerNumber == 1 ? 2 : 1);
            printGameSummary(&player1, &player2);
            return 1;
        }
    }

    /* R3 超时判分 */
    printf("\n===== %d 手预算用完，进入超时判分 =====\n", TURN_BUDGET);
    printStatus(&player1, 1);
    printStatus(&player2, 2);
    int winner = judgeByDeadline(&player1, &player2);
    if (winner == 0) {
        printf("双方基地生命值与剩余兵力均相同 —— 判和棋。\n");
    } else {
        printf("玩家%d获胜！（超时判分：基地血 %d:%d，剩余兵力 %d:%d）\n",
               winner, player1.baseHealth, player2.baseHealth,
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
