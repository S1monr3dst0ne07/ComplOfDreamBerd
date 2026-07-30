

#include <platform.h>
#include <object.h>
#include <ht.h>


object_t _print(object_t obj)
{

    hti iter;
    ht_entry* ent;
    switch (obj->kind)
    {
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


