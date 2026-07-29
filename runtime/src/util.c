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
    while (*msg)
        outchar(*msg++);
}



#endif
