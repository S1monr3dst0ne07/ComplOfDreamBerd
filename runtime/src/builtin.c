

#include <platform.h>
#include <object.h>
#include <ht.h>


object_t _print(object_t obj)
{

    hti iter;
    ht_entry* ent;
    switch (obj->kind)
    {
        case KIND_UNDEFINED:
            putstr("undefined");
            break;
        case KIND_INT:
            putstr(single_int_to_string((uint64_t)obj->data));
            break;
        case KIND_STRING:
            iter = ht_iterator(obj->data);
            while ((ent = ht_count(&iter)))
                outchar((char)(uint64_t)ent->value->data);
            break;

        case KIND_DICT:
            iter = ht_iterator(obj->data);
            outchar('{');
            while ((ent = ht_next(&iter)))
            {
                _print(ent->key);
                outchar(':');
                _print(ent->value);
                putstr(", ");
            }
            outchar('}');
            break;

        case KIND_ARRAY:
            iter = ht_iterator(obj->data);
            outchar('[');
            while ((ent = ht_count(&iter)))
            {
                _print(ent->value);
                putstr(", ");
            }
            outchar(']');
            break;

        case KIND_FLOAT:
            double value = util_voidptr_to_float(obj->data);
            int64_t real = (int64_t) value;
            double frac = value - (double)real;

            putstr(single_int_to_string(real));
            outchar('.');
            while (frac != (int64_t)frac) frac *= 10;
            putstr(single_int_to_string(frac));
            break;


        default:
            debug("_print impl\n");
    }
}


object_t db_func_print(object_t obj)
{
    _print(obj);
    outchar('\n');

    // refernces always goes out of scope
    obj_dec(obj);

    return obj_create(KIND_UNDEFINED, 0);
}


object_t db_func_undefined()
{
    return obj_create(KIND_UNDEFINED, 0);
}


object_t db_func_readline()
{
    static char buf[4096];
    char* ptr = buf;

    char c;
    while ((c = inchar()) != '\n')
        *ptr++ = c;

    *ptr = '\0';
    return util_create_string(buf);
}

object_t db_func_sqrt(object_t x)
{
    debug("IMPL db_func_sqrt\n");
    return x;
}
object_t db_func_push(object_t base, object_t elem)
{
    ht* table = (ht*)base->data;
    uint64_t index = table->length;
    obj_dec(base);

    ht_set(table, obj_create(KIND_INT, (void*)index), elem);

    return obj_create(KIND_UNDEFINED, 0);
}
object_t db_func_length(object_t array)
{
    if (array->kind != KIND_ARRAY)
        goto error;

    uint64_t len = ((ht*)array->data)->length;
    obj_dec(array);

    return obj_create(KIND_INT, (void*)len);

error:
    return obj_create(KIND_UNDEFINED, 0);
}



