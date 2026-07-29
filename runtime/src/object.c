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

        // one reference by caller 
        // otherwise object would be drop immediately
    obj->ref  = 1; 

    _obj_count++;
    return obj;
}

void obj_del(object_t obj)
{
    switch (obj->kind)
    {
        case KIND_INT:
            free(obj);
            break;
        case KIND_STRING:
            ht_del(obj->data);
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


void obj_inc(object_t obj)
{
    obj->ref++;
}
void obj_dec(object_t obj)
{
    obj->ref--;
    if (obj->ref == 0) 
        obj_del(obj);
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
        case KIND_INT: return (uint64_t)obj->data;
            
        default:
            debug("TOOD: implement obj_hash\n");
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
        default:
            debug("TOOD: implement obj_cmp\n");
            break;
    }
    return false;
}


#endif
