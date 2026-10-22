/* SPDX-License-Identifier: 0BSD */
/* ncurses port test: the compiled-in terminal descriptions. */
#include <curses.h>
#include <stdio.h>
#include <term.h>

int main(void)
{
    int err;
    if (setupterm("xterm-256color", 1, &err) != OK)
        return 1;
    printf("ncurses: %s, xterm-256color has %d colours\n", curses_version(), tigetnum("colors"));
    const char *cup = tigetstr("cup");
    if (!cup || cup == (char *) -1)
        return 2;
    if (setupterm("vt100", 1, &err) != OK)
        return 3;
    printf("ncurses: vt100 clear is %s\n", tigetstr("clear") ? "known" : "missing");
    printf("ncurses: OK\n");
    return 0;
}
