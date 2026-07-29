#ifndef _H_HT
#define _H_HT


typedef struct {
    object_t key;
    object_t value;
} ht_entry;

typedef struct ht {
    ht_entry* entries;
    size_t capacity;
    size_t length;
} ht;


ht* ht_create(void);
void ht_del(ht* table);
void* ht_get(ht* table, object_t key);
void ht_set(ht* table, object_t key, object_t value);

#endif
