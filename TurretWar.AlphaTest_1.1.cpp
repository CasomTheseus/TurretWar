#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

typedef struct {
    int baseHealth;
    int turretCount;
    int shieldCount;
    int totalShieldsBuilt;
    int totalTurretsBuilt;
    int totalDamageDealt;
} Player;

void printStatus(Player *player, int playerNumber) {
    printf("玩家%d状态：基地生命值：%d，炮台数量：%d，护盾数量：%d\n",
           playerNumber, player->baseHealth, player->turretCount, player->shieldCount);
}

void buildTurret(Player *player) {
    player->turretCount++;
    player->totalTurretsBuilt++; // 累计炮台量
}

void buildShield(Player *player) {
    player->shieldCount += 2;
    player->totalShieldsBuilt += 2; // 累计护盾量
}

void attack(Player *attacker, Player *defender) {
    int damage = attacker->turretCount;
    attacker->totalDamageDealt += damage; // 累计伤害量

    while (damage > 0 && defender->baseHealth > 0) {
        if (defender->shieldCount > 0) {
            defender->shieldCount--;
        } else if (defender->turretCount > 0) {
            defender->turretCount--;
        } else {
            defender->baseHealth--;
        }
        damage--;
    }
}

void printGameSummary(Player *player1, Player *player2) {
    printf("\n===== 游戏结算 =====\n");
    usleep(1000000);
    printf("玩家1累计建造护盾量：%d\n", player1->totalShieldsBuilt);
    printf("玩家1累计建造炮台量：%d\n", player1->totalTurretsBuilt);
    printf("玩家1累计造成伤害量：%d\n", player1->totalDamageDealt);
    printf("------------------------\n");
    usleep(1000000);
    printf("玩家2累计建造护盾量：%d\n", player2->totalShieldsBuilt);
    printf("玩家2累计建造炮台量：%d\n", player2->totalTurretsBuilt);
    printf("玩家2累计造成伤害量：%d\n", player2->totalDamageDealt);
    printf("====================\n");
    sleep(2);
}
void printAuthorInfo() {
    printf("\n==========游戏信息==========\n");
    usleep(500000);
    printf("Gamename:TurretWar,炮台战争\n");
    usleep(500000);
    printf("GameVersion:AlphaTest_1.1\n");
    usleep(500000);
    printf("\n==========作者信息==========\n");
    printf("GameDeveloper:QuanYuhang XuDalin JiangHaoyu RenXinduo WangKewei Wangruiqi\n");
    usleep(250000);
    printf("Game Inspiration Proposer：QuanYuhang\n");
    usleep(250000);
    printf("Code By:Casom Theseus\n");
    usleep(250000);
    printf("Thanks for your playing!\n");
    usleep(250000);
    printf("==========END==========");



}

int main() {
    srand(time(NULL));
    Player player1 = {3, 0, 0, 0, 0, 0}; // 初始化玩家1
    Player player2 = {3, 0, 0, 0, 0, 0}; // 初始化玩家2
    Player *currentAttacker = &player1;
    Player *currentDefender = &player2;
    int choice;
    char rules[] =
        "游戏规则说明：\n\n"
        "欢迎来到炮台战争！以下是游戏的基本规则：\n\n"
        "1. 初始设置：\n"
        "   - 每位玩家的基地生命值初始为3，且无法补充。\n"
        "   - 炮台数量和护盾数量初始均为0。\n\n"
        "2. 玩家行动：\n"
        "   - 每次随机选择一名玩家进行行动。\n"
        "   - 行动时，玩家可以选择以下三种操作之一：\n"
        "     - 建造炮台：增加1个炮台。\n"
        "     - 建造护盾：增加2个护盾。\n"
        "     - 发起进攻：使用所有炮台对敌方进行攻击，每个炮台发射一枚炮弹。\n\n"
        "3. 伤害计算：\n"
        "   - 当造成伤害时，首先减少敌方的护盾数量。\n"
        "   - 如果护盾归零，继续攻击敌方的炮台。\n"
        "   - 如果炮台也归零，最后攻击敌方的基地。\n\n"
        "4. 胜负判定：\n"
        "   - 当一方的基地生命值降至0或以下时，该玩家失败，游戏结束。\n\n"
        "请确保在行动时立即执行选择的操作，无法存储行动。\n\n"
        "祝你游戏愉快！\n";
    printf("%s", rules);
    printf("欢迎来到炮台战争！\n");
    fflush(stdout);
    sleep(2);
    printf("敌军还有五秒到达战场，请做好准备！\n");
    fflush(stdout);
    sleep(5);
    printf("全军出击！\n");
    fflush(stdout);
    sleep(2);

    while (player1.baseHealth > 0 && player2.baseHealth > 0) {
        // 随机选择当前行动玩家
        int currentPlayerNumber = rand() % 2 + 1; // 随机生成1或2
        Player *currentAttacker = (currentPlayerNumber == 1) ? &player1 : &player2;
        Player *currentDefender = (currentPlayerNumber == 1) ? &player2 : &player1;

        printStatus(currentAttacker, currentPlayerNumber);
        printStatus(currentDefender, currentPlayerNumber == 1 ? 2 : 1);
        printf("玩家%d的回合，请选择行动：\n", currentPlayerNumber);
        printf("1. 建造炮台;\n");
        printf("2. 建造护盾;\n");
        printf("3. 发起进攻;\n");
        printf("请做出玩家%d的选择：", currentPlayerNumber);
        scanf("%d", &choice);

        switch (choice) {
            case 1:
                buildTurret(currentAttacker);
            break;
            case 2:
                buildShield(currentAttacker);
            break;
            case 3:
                attack(currentAttacker, currentDefender);
            break;
            default:
                printf("无效的选择，请重新输入。\n");
            continue;
        }

        // 检查防守方是否被击败
        if (currentDefender->baseHealth <= 0) {
            printf("玩家%d获胜！\n", currentPlayerNumber);
            break;
        }
    }

    //Summary Unit
    printGameSummary(&player1, &player2);
    printAuthorInfo();

    return 0;
}