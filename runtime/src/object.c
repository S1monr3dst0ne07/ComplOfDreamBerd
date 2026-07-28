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


object_t create_object(kind_t kind, void* data)
{
    object_t obj = malloc(sizeof(struct _object_s));
    obj->kind = kind;
    obj->data = data;

        // one reference by caller 
        // otherwise object would be drop immediately
    obj->ref  = 1; 
    return obj;
}




#endif
