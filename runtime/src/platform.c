
#include <stdint.h>
#include <stddef.h>

// warning: operating system stuff ahead.
// this file contains syscall bindings
// and a small user heap for linux.

// https://filippo.io/linux-syscall-table/
enum
{
    SYS_WRITE = 1,
    SYS_BRK   = 12,
};

#define SYS_CLOBBERS "rcx","r11","memory"
#define SYS_STDOUT 1


void outchar(char c)
{
    asm volatile (
        "syscall"
        : : "a"(SYS_WRITE), "D"(SYS_STDOUT), "S"(&c), "d"(1)
        : SYS_CLOBBERS
    );
}

uintptr_t brk(uintptr_t new)
{
    uintptr_t old;
    asm volatile (
        "syscall"
        : "=a"(old)
        : "a"(SYS_BRK), "D"(new)
        : SYS_CLOBBERS
    );
    return old;
}



uintptr_t current_break;

void init()
{
}


void* malloc(size_t bytes)
{
}

