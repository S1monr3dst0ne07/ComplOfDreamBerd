#ifndef _G_UTIL
#define _G_UTIL

#include <object.c>
#include <ht.c>

object_t util_create_string(const char* ptr)
{
    ht* table = ht_create();

    for (size_t i = 0; ptr[i]; i++)
    {
        object_t key = obj_create(KIND_INT, (void*)i);
        ht_set(table, 
            key,
            obj_create(KIND_INT, (void*)(uint64_t)ptr[i])
        );

        // the hash table make sure the object will
        // stay alive if it needs a refernce to it.
        // otherwise, the key has no refernces.
        obj_dec(key);
    }

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

static bool _is_container(object_t x)
{
    switch (x->kind)
    {
        case KIND_DICT:
        case KIND_STRING:
            return true;
        default:
            return false;
    }
}


void util_set_ht(object_t table_obj, object_t key, object_t value)
{
    if (!_is_container(table_obj))
        goto not_a_table;
    ht* table = table_obj->data;

    ht_set(table, key, value);
not_a_table:
    obj_dec(key);
    return;
}
object_t util_get_ht(object_t table_obj, object_t key)
{
    if (!_is_container(table_obj))
        goto not_a_table;
    ht* table = table_obj->data;

    object_t deep = ht_get(table, key);
    if (!deep) goto entry_not_found;
    obj_dec(key);
    return deep;

entry_not_found:
not_a_table:
    obj_dec(key);
    return obj_create(KIND_UNDEFINED, 0);
}


enum op_kind_e
{
    OP_PLUS = 1,
    OP_MINUS,
    OP_TIMES,
    OP_EQUAL,
    OP_INEQUAL,
};

object_t util_operate(object_t a, object_t b, enum op_kind_e op)
{
    #define VAL(x) ((uint64_t)x->data)
    #define obj_create_cast(kind, x) (obj_create(kind, (void*)(x)))

    object_t ret;
    switch (op)
    {
        case OP_PLUS:    ret = obj_create_cast(KIND_INT, VAL(a) + VAL(b)); break;
        case OP_MINUS:   ret = obj_create_cast(KIND_INT, VAL(a) - VAL(b)); break;
        case OP_TIMES:   ret = obj_create_cast(KIND_INT, VAL(a) * VAL(b)); break;
        case OP_EQUAL:   ret = obj_create_cast(KIND_INT, obj_cmp(a, b)); break;
        case OP_INEQUAL: ret = obj_create_cast(KIND_INT, (uint64_t)!obj_cmp(a, b)); break;
    }

    obj_dec(a);
    obj_dec(b);
    return ret;
}



#endif
