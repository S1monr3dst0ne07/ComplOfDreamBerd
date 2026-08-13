

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


        default:
            debug("_print impl\n");
    }
}


object_t print(object_t obj)
{
    _print(obj);
    outchar('\n');

    // refernces always goes out of scope
    obj_dec(obj);

    return obj_create(KIND_UNDEFINED, 0);
}


object_t undefined()
{
    return obj_create(KIND_UNDEFINED, 0);
}


object_t readline()
{
    static char buf[4096];
    char* ptr = buf;

    char c;
    while ((c = inchar()) != '\n')
        *ptr++ = c;

    *ptr = '\0';
    return util_create_string(buf);
}

object_t sqrt(object_t x)
{
    return x;
}



