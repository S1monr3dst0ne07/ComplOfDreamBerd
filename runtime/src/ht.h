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


typedef struct {
    ht*     table; 
    int64_t index; 
        // current index into ht->entries.
        // -1 for uninited.
} hti;


hti       ht_iterator(ht* table);
ht_entry* ht_next(hti* it);
ht_entry* ht_count(hti* it);

uint64_t ht_hash(ht* table);


#endif
