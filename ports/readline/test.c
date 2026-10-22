/* SPDX-License-Identifier: 0BSD */
/* readline port test: one edited line and the history. */
#include <stdio.h>
#include <stdlib.h>
#include <readline/history.h>
#include <readline/readline.h>

int main(void)
{
    printf("readline: %s, type a line\n", rl_library_version);
    fflush(stdout);
    char *line = readline("> ");
    if (!line)
        return 1;
    add_history(line);
    printf("readline: got [%s], history %d\n", line, history_length);
    free(line);
    printf("readline: OK\n");
    return 0;
}
