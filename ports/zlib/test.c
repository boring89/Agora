/* SPDX-License-Identifier: 0BSD */
/* zlib port test: compress and uncompress a buffer, CRC-32. */
#include <stdio.h>
#include <string.h>
#include <zlib.h>

int main(void)
{
    char text[4096], back[4096];
    unsigned char packed[8192];
    for (int i = 0; i < (int) sizeof text; i++)
        text[i] = "STELA zlib "[i % 11];
    uLongf plen = sizeof packed, blen = sizeof back;
    if (compress2(packed, &plen, (const Bytef *) text, sizeof text, 9) != Z_OK)
        return 1;
    if (uncompress((Bytef *) back, &blen, packed, plen) != Z_OK || blen != sizeof text
        || memcmp(text, back, sizeof text) != 0)
        return 2;
    printf("zlib: %s, 4096 -> %lu bytes\n", zlibVersion(), (unsigned long) plen);
    printf("zlib: crc %08lx\n", crc32(0, (const Bytef *) "123456789", 9));
    printf("zlib: OK\n");
    return 0;
}
