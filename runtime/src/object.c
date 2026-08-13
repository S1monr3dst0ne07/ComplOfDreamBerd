#ifndef _G_OBJECT
#define _G_OBJECT


#include <stdint.h>
#include <stdbool.h>

#include <object.h>
#include <platform.h>
#include <ht.h>
#include <util.h>


static uint32_t _obj_count = 0;

object_t obj_create(kind_t kind, void* data)
{
    object_t obj = malloc(sizeof(struct _object_s));
    obj->kind = kind;
    obj->data = data;
    obj->ref  = 0;

    // one reference by caller 
    // otherwise object would be drop immediately
    obj_inc(obj);

    _obj_count++;
    return obj;
}

void obj_del(object_t obj)
{
    switch (obj->kind)
    {
        case KIND_UNDEFINED:
        case KIND_INT:
            free(obj);
            break;
        case KIND_STRING:
        case KIND_DICT:
            ht_del(obj->data);
            free(obj);
            break;
        default:
            debug("TOOD: implement obj_del\n");
            break;
    }
    _obj_count--;
}

void* obj_unwrap(object_t obj)
{
    return obj->data;
}

void debug_update(object_t obj)
{
    debug(single_int_to_string((uint64_t)obj));
    debug("\n");
    debug(single_int_to_string(obj->ref));
    debug("\n");
}


void obj_inc(object_t obj)
{
    if (obj)
        obj->ref++;
    else
        debug("obj_inc NULL\n");
    
    debug_update(obj);
}
void obj_dec(object_t obj)
{
    if (obj)
    {
        obj->ref--;
        if (obj->ref == 0)
            obj_del(obj);
    }
    else
        debug("obj_dec NULL\n");

    debug_update(obj);
}

void* obj_dec_unwrap(object_t obj)
{
    void* data = obj->data;
    obj_dec(obj);
    return data;
}


uint64_t debug_get_obj_count(void)
{
    return _obj_count;
}


uint64_t obj_hash(object_t obj)
{
    switch (obj->kind)
    {
        case KIND_UNDEFINED: return 0;
        case KIND_INT:       return (uint64_t)obj->data;
        case KIND_DICT: 
        case KIND_STRING: 
            return ht_hash(obj->data);
            
        default:
            debug("TOOD: implement obj_hash\n");
            debug(single_int_to_string(obj->kind));
            break;
    }
    return 0;
}
bool obj_cmp(object_t a, object_t b)
{
    if (a->kind != b->kind)
        return false;

    switch (a->kind)
    {
        case KIND_UNDEFINED: return true;
        case KIND_INT: return a->data == b->data;
        case KIND_DICT:
        case KIND_STRING:
            return ht_cmp(a->data, b->data);


        default:
            debug("TOOD: implement obj_cmp\n");
            break;
    }
    return false;
}

#endif
