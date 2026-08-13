#ifndef _H_OBJECT
#define _H_OBJECT

typedef enum 
{
    KIND_UNDEFINED,
    KIND_INT,
    KIND_STRING,
    KIND_ARRAY,
    KIND_DICT,
    KIND_FLOAT,
} kind_t;


typedef struct _object_s
{
    kind_t   kind;
    void*    data;
    uint32_t ref; 
} *object_t;



object_t obj_create(kind_t kind, void* data);
void obj_del(object_t obj);
void* obj_unwrap(object_t obj);
void obj_inc(object_t obj);
void obj_dec(object_t obj);
void* obj_dec_unwrap(object_t obj);
uint64_t debug_get_obj_count(void);
uint64_t obj_hash(object_t obj);
bool obj_cmp(object_t a, object_t b);

#endif
