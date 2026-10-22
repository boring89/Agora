/* SPDX-License-Identifier: 0BSD */
/* Mbed TLS port test: SHA-256 and an AES-128-GCM round trip. */
#include <mbedtls/gcm.h>
#include <mbedtls/sha256.h>
#include <mbedtls/version.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    unsigned char hash[32];
    if (mbedtls_sha256((const unsigned char *) "abc", 3, hash, 0) != 0)
        return 1;
    printf("mbedtls: %s, sha256(abc) = %02x%02x%02x%02x...\n", MBEDTLS_VERSION_STRING, hash[0],
           hash[1], hash[2], hash[3]);
    unsigned char key[16] = {1}, iv[12] = {2}, text[64], sealed[64], opened[64], tag[16];
    memset(text, 'S', sizeof text);
    mbedtls_gcm_context gcm;
    mbedtls_gcm_init(&gcm);
    if (mbedtls_gcm_setkey(&gcm, MBEDTLS_CIPHER_ID_AES, key, 128) != 0)
        return 2;
    if (mbedtls_gcm_crypt_and_tag(&gcm, MBEDTLS_GCM_ENCRYPT, sizeof text, iv, sizeof iv, NULL, 0,
                                  text, sealed, sizeof tag, tag) != 0)
        return 3;
    if (mbedtls_gcm_auth_decrypt(&gcm, sizeof text, iv, sizeof iv, NULL, 0, tag, sizeof tag,
                                 sealed, opened) != 0 || memcmp(text, opened, sizeof text) != 0)
        return 4;
    sealed[3] ^= 1;
    if (mbedtls_gcm_auth_decrypt(&gcm, sizeof text, iv, sizeof iv, NULL, 0, tag, sizeof tag,
                                 sealed, opened) == 0)
        return 5;
    mbedtls_gcm_free(&gcm);
    printf("mbedtls: AES-GCM round trip and tamper check ok\n");
    printf("mbedtls: OK\n");
    return 0;
}
