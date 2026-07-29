

#include <platform.h>
#include <object.h>
#include <ht.h>


object_t print(object_t obj)
{
    // refernces always goes out of scope
    obj_dec(obj);

    switch (obj->kind)
    {
        case KIND_INT:
            putstr(single_int_to_string((uint64_t)obj->data));
            break;
        case KIND_STRING:
            hti iter = ht_iterator(obj->data);
            ht_entry* ent;
            while ((ent = ht_count(&iter)))
                outchar((char)(uint64_t)ent->value->data);
            outchar('\n');
            break;
            
    }

    return obj_create(KIND_UNDEFINED, 0);
}




