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
    printf("���%d״̬����������ֵ��%d����̨������%d������������%d\n",
           playerNumber, player->baseHealth, player->turretCount, player->shieldCount);
}

void buildTurret(Player *player) {
    player->turretCount++;
    player->totalTurretsBuilt++;
}

void buildShield(Player *player) {
    player->shieldCount += 2;
    player->totalShieldsBuilt += 2;
}

void attack(Player *attacker, Player *defender) {
    int damage = attacker->turretCount;
    attacker->totalDamageDealt += damage;

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
    printf("\n===== ��Ϸ���� =====\n");
    usleep(1000000);
    printf("���1�ۼƽ��커������%d\n", player1->totalShieldsBuilt);
    printf("���1�ۼƽ�����̨����%d\n", player1->totalTurretsBuilt);
    printf("���1�ۼ�����˺�����%d\n", player1->totalDamageDealt);
    printf("------------------------\n");
    usleep(1000000);
    printf("���2�ۼƽ��커������%d\n", player2->totalShieldsBuilt);
    printf("���2�ۼƽ�����̨����%d\n", player2->totalTurretsBuilt);
    printf("���2�ۼ�����˺�����%d\n", player2->totalDamageDealt);
    printf("====================\n");
    sleep(2);
}

void printAuthorInfo() {
    printf("\n==========��Ϸ��Ϣ==========\n");
    usleep(500000);
    printf("Gamename:TurretWar,��̨ս��\n");
    usleep(500000);
    printf("GameVersion:AlphaTest_1.2\n");
    usleep(500000);
    printf("\n==========������Ϣ==========\n");
    printf("GameDeveloper:QuanYuhang XuDalin JiangHaoyu RenXinduo WangKewei Wangruiqi\n");
    usleep(250000);
    printf("Game Inspiration Proposer��QuanYuhang\n");
    usleep(250000);
    printf("Code By:Casom Theseus\n");
    usleep(250000);
    printf("Thanks for your playing!\n");
    usleep(250000);
    printf("==========END==========");
}

void printRules() {
    char rules[] =
        "��Ϸ����˵����\n\n"
        "��ӭ������̨ս������������Ϸ�Ļ�������\n\n"
        "1. ��ʼ���ã�\n"
        "   - ÿλ��ҵĻ�������ֵ��ʼΪ3�����޷����䡣\n"
        "   - ��̨�����ͻ���������ʼ��Ϊ0��\n\n"
        "2. ����ж���\n"
        "   - ÿ�����ѡ��һ����ҽ����ж���\n"
        "   - �ж�ʱ����ҿ���ѡ���������ֲ���֮һ��\n"
        "     - ������̨������1����̨��\n"
        "     - ���커�ܣ�����2�����ܡ�\n"
        "     - ���������ʹ��������̨�Եз����й�����ÿ����̨����һö�ڵ���\n\n"
        "3. �˺����㣺\n"
        "   - ������˺�ʱ�����ȼ��ٵз��Ļ���������\n"
        "   - ������ܹ��㣬���������з�����̨��\n"
        "   - �����̨Ҳ���㣬��󹥻��з��Ļ��ء�\n\n"
        "4. ʤ���ж���\n"
        "   - ��һ���Ļ�������ֵ����0������ʱ�������ʧ�ܣ���Ϸ������\n\n"
        "��ȷ�����ж�ʱ����ִ��ѡ��Ĳ������޷��洢�ж���\n\n"
        "ף����Ϸ��죡\n";
    printf("%s", rules);
}

void resetPlayers(Player *player1, Player *player2) {
    player1->baseHealth = 3;
    player1->turretCount = 0;
    player1->shieldCount = 0;

    player2->baseHealth = 3;
    player2->turretCount = 0;
    player2->shieldCount = 0;
}

void playGame(int showRules) {
    srand(time(NULL));
    Player player1 = {3, 0, 0, 0, 0, 0};
    Player player2 = {3, 0, 0, 0, 0, 0};

    if (showRules) {
        printRules();
    }

    printf("��ӭ������̨ս����\n");
    fflush(stdout);
    sleep(2);
    printf("�о��������뵽��ս����������׼����\n");
    fflush(stdout);
    sleep(5);
    printf("ȫ��������\n");
    fflush(stdout);
    sleep(2);

    while (player1.baseHealth > 0 && player2.baseHealth > 0) {
        int currentPlayerNumber = rand() % 2 + 1;
        Player *currentAttacker = (currentPlayerNumber == 1) ? &player1 : &player2;
        Player *currentDefender = (currentPlayerNumber == 1) ? &player2 : &player1;

        printStatus(currentAttacker, currentPlayerNumber);
        printStatus(currentDefender, currentPlayerNumber == 1 ? 2 : 1);
        printf("���%d�Ļغϣ���ѡ���ж���\n", currentPlayerNumber);
        printf("1. ������̨;\n");
        printf("2. ���커��;\n");
        printf("3. �������;\n");
        printf("���������%d��ѡ��", currentPlayerNumber);
        int choice;
		while(1){
			if(scanf("%d", &choice)!=1){
        	printf("��������ȷָ��\n");
        	fflush(stdin);
			}else{
				break;
			};
		};//��Ч�Լ�� 
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
                printf("��Ч��ѡ�����������롣\n");
                continue;
        }

        if (currentDefender->baseHealth <= 0) {
            printf("���%d��ʤ��\n", currentPlayerNumber);
            break;
        }
    }

    printGameSummary(&player1, &player2);
}

int main() {
    int playAgain = 1;
    int firstGame = 1;

    while (playAgain) {
        if (firstGame) {
            playGame(1);
            firstGame = 0;
        } else {
            playGame(0);
        }

        printf("\n�Ƿ���ս��\n");
        printf("1. ��ս\n");
        printf("0. �˳�\n");
        printf("��ѡ��");
        int choice;
        while(1){
			if(scanf("%d", &choice)!=1){
        	printf("��������ȷָ��\n");
        	fflush(stdin);
			}else{
				break;
			};
		};//��Ч�Լ�� 

        if (choice != 1) {
            playAgain = 0;
            printAuthorInfo();
        }
    }

    return 0;
}
