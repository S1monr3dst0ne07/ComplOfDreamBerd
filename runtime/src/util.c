#ifndef _G_UTIL
#define _G_UTIL

#include <object.c>
#include <ht.c>

// NOTE: the default reference convention
// is move-on-call ALWAYS!

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


char* single_int_to_string(int64_t x)
{
    static char buffer[64];
    char* iter = buffer + sizeof(buffer);

    #define WRITE(c) (*(--iter)) = c

    bool sign = x < 0;
    if (sign) x = -x;

    WRITE('\0');
    if (!x) WRITE('0');
    while (x)
    {
        WRITE((x % 10) + '0');
        x = x / 10;
    }

    if (sign) WRITE('-');

    return iter;
}

static bool _is_container(object_t x)
{
    switch (x->kind)
    {
        case KIND_DICT:
        case KIND_STRING:
        case KIND_ARRAY:
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
    return;

not_a_table:
    putstr("Runtime Error: Trying to set element of non-table object.\n");
}
object_t util_get_ht(object_t table_obj, object_t key)
{
    if (!_is_container(table_obj))
        goto not_a_table;

    ht* table = table_obj->data;
    object_t elem = ht_get(table, key);

    if (!elem) goto entry_not_found;
    obj_inc(elem);
    goto done;

not_a_table:
    putstr("Runtime Error: Trying to get element of non-table object.\n");
entry_not_found:
    elem = obj_create(KIND_UNDEFINED, 0);

done:
    obj_dec(key);
    return elem;
}


enum op_kind_e
{
    OP_PLUS = 1,
    OP_MINUS,
    OP_TIMES,
    OP_DIVIDE,
    OP_POWER,
    OP_EQUAL,
    OP_INEQUAL,
    OP_NEGATE,
    OP_LESSER,
    OP_GREATER,
};

int64_t util_operate_int(int64_t a, int64_t b, enum op_kind_e op)
{
    switch (op)
    {
        case OP_PLUS:    return a + b;
        case OP_MINUS:   return a - b;
        case OP_TIMES:   return a * b;
        case OP_DIVIDE:  return a / b;
        case OP_NEGATE:  return -a;
        case OP_LESSER:  return a < b;
        case OP_GREATER: return a > b;

        default:
            debug("util_operate_int IMPL\n");
    }
}

void util_cast_int_to_float(object_t x)
{
    int64_t val = (int64_t)x->data;
    double  real = (float)val;
    
    double* trick = &real;
    x->data = *(void**)trick;

}

void util_type_coerce(object_t a, object_t b)
{
    enum op_kind_e x = a->kind;
    enum op_kind_e y = b->kind;

    // type agreement, good, done.
    if (x == y) return;

    // int op float.
    if (x == KIND_INT && y == KIND_FLOAT) util_cast_int_to_float(a);
    if (x == KIND_FLOAT && y == KIND_INT) util_cast_int_to_float(b);
}


object_t util_operate(object_t b, object_t a, enum op_kind_e op)
{
    #define obj_data(x) ((int64_t)x->data)
    #define obj_create_cast(kind, x) (obj_create(kind, (void*)(x)))
    

    object_t ret;

    // object equality is type agnostic.
    /**/ if (op == OP_EQUAL)   ret = obj_create_cast(KIND_INT, obj_cmp(a, b));
    else if (op == OP_INEQUAL) ret = obj_create_cast(KIND_INT, (uint64_t)!obj_cmp(a, b));
    else {
        util_type_coerce(a, b);

        if (a->kind != b->kind)
            goto type_mismatch;


        switch(a->kind)
        {
            case KIND_INT: 
                ret = obj_create_cast(
                    KIND_INT, 
                    util_operate_int(
                        (int64_t)a->data, 
                        (int64_t)b->data, 
                        op
                    )
                );
                break;
        }
    }

    obj_dec(a);
    obj_dec(b);
    return ret;

type_mismatch:
    putstr("Runtime Error: Arithemtic operation, type mismatch.\n");
    putstr(single_int_to_string(a->kind));
    putstr("\n");
    putstr(single_int_to_string(b->kind));
    putstr("\n");
    return obj_create(KIND_UNDEFINED, 0);
}



#endif
