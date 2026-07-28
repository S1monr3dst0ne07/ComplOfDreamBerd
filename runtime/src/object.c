

#include <stdint.h>
#include <platform.c>

typedef enum 
{
    KIND_UNINIT,
    KIND_STRING,
} kind_t;


typedef struct _object_s
{
    kind_t   type;
    void*    data;
    uint32_t ref; 
} *object_t;


object_t create_object()
{
    object_t obj = malloc(sizeof(struct _object_s));
    obj->type = KIND_UNINIT;
    obj->data = NULL;
        // one reference by caller 
        // otherwise object would be drop immediately
    obj->ref  = 1; 
    return obj;
}




