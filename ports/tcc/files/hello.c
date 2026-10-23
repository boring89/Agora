#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    char buf[32];
    snprintf(buf, sizeof buf, "%d+%d=%d", 20, 22, 20 + 22);
    printf("tcc: compiled on STELA, %s, %zu chars, %d args\n", buf, strlen(buf), argc);
    return 0;
}
