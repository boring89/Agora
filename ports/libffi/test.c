/* SPDX-License-Identifier: 0BSD */
/* libffi port test: call functions through ffi_call. */
#include <ffi.h>
#include <stdio.h>

static long add3(int a, long b, short c) { return a + b + c; }
static double scale(double x, float y) { return x * y; }

int main(void)
{
    ffi_cif cif;
    ffi_type *args[3] = {&ffi_type_sint, &ffi_type_slong, &ffi_type_sshort};
    if (ffi_prep_cif(&cif, FFI_DEFAULT_ABI, 3, &ffi_type_slong, args) != FFI_OK)
        return 1;
    int a = 40;
    long b = 1000;
    short c = 2;
    void *values[3] = {&a, &b, &c};
    ffi_arg r;
    ffi_call(&cif, FFI_FN(add3), &r, values);
    printf("libffi: add3 = %ld\n", (long) r);
    ffi_type *dargs[2] = {&ffi_type_double, &ffi_type_float};
    if (ffi_prep_cif(&cif, FFI_DEFAULT_ABI, 2, &ffi_type_double, dargs) != FFI_OK)
        return 2;
    double x = 2.5;
    float y = 4.0f;
    void *dv[2] = {&x, &y};
    double d;
    ffi_call(&cif, FFI_FN(scale), &d, dv);
    printf("libffi: scale = %.1f\n", d);
    printf("libffi: OK\n");
    return (long) r == 1042 && d == 10.0 ? 0 : 3;
}
