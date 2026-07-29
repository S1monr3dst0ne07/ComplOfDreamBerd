#ifndef _G_UTIL
#define _G_UTIL

#include <object.c>
#include <ht.c>

object_t util_create_string(const char* ptr)
{
    ht* table = ht_create();

    for (size_t i = 0; ptr[i]; i++)
        ht_set(table, 
            obj_create(KIND_INT, (void*)i), 
            obj_create(KIND_INT, (void*)(uint64_t)ptr[i])
        );

    return obj_create(KIND_STRING, table);
}

void debug(const char* msg)
{
    putstr(msg);
}

void putstr(const char* msg)
{
    while (*msg)
        outchar(*msg++);
    outchar('\n');
}


char* single_int_to_string(uint64_t x)
{
    static char buffer[64];
    char* iter = buffer + sizeof(buffer);

    #define WRITE(c) (*(--iter)) = c

    WRITE('\0');
    if (!x) WRITE('0');
    while (x)
    {
        WRITE((x % 10) + '0');
        x = x / 10;
    }

    return iter;
}



#endif
