#ifndef _G_OBJECT
#define _G_OBJECT


#include <stdint.h>
#include <platform.c>

typedef enum 
{
    KIND_UNINIT,
    KIND_INT,
    KIND_STRING,
} kind_t;


typedef struct _object_s
{
    kind_t   kind;
    void*    data;
    uint32_t ref; 
} *object_t;

static uint32_t obj_count = 0;

object_t create_object(kind_t kind, void* data)
{
    object_t obj = malloc(sizeof(struct _object_s));
    obj->kind = kind;
    obj->data = data;

        // one reference by caller 
        // otherwise object would be drop immediately
    obj->ref  = 1; 

    obj_count++;
    return obj;
}

void delete_object(object_t obj)
{
    switch (obj->kind)
    {
        case KIND_INT:
            free(obj);
            break;
    }
    obj_count--;
}

void* deref_object(object_t obj)
{
    return obj->data;
}

void ref_inc(object_t obj)
{
    obj->ref++;
}
void ref_dec(object_t obj)
{
    obj->ref--;
    if (obj->ref == 0) 
        delete_object(obj);
}





#endif
