#ifndef _G_HT
#define _G_HT

#include <stdint.h>
#include <stdbool.h>

#include <ht.h>

#define INITIAL_CAPACITY 16  // must not be zero

ht* ht_create(void) 
{
    ht* table = malloc(sizeof(ht));
    table->length = 0;
    table->capacity = INITIAL_CAPACITY;

    size_t bytes = table->capacity * sizeof(ht_entry);
    table->entries = malloc(bytes);
    memset(table->entries, 0, bytes);

    return table;
}

void ht_del(ht* table) 
{
    for (size_t i = 0; i < table->capacity; i++) 
    {
        ht_entry ent = table->entries[i];
        if (!ent.key) continue;

        obj_dec(ent.key);
        obj_dec(ent.value);
    }

    free(table->entries);
    free(table);
}


/*
#define FNV_OFFSET 14695981039346656037UL
#define FNV_PRIME 1099511628211UL

// Return 64-bit FNV-1a hash for key (NUL-terminated). See description:
// https://en.wikipedia.org/wiki/Fowler–Noll–Vo_hash_function
static uint64_t hash_key(const char* key) {
    uint64_t hash = FNV_OFFSET;
    for (const char* p = key; *p; p++) {
        hash ^= (uint64_t)(unsigned char)(*p);
        hash *= FNV_PRIME;
    }
    return hash;
}
*/

void* ht_get(ht* table, object_t key) 
{
    // table capacity is always power of two.
    uint64_t hash = obj_hash(key);
    size_t index = (size_t)(hash & (uint64_t)(table->capacity - 1));

    ht_entry ent;
    while ((ent = table->entries[index]).key) 
    {
        if (obj_cmp(key, ent.key)) 
            return ent.value;

        if (++index >= table->capacity) index = 0;
    }
    return NULL;
}

// Internal function to set an entry (without expanding table).
static object_t ht_set_entry(ht_entry* entries, size_t capacity, object_t key, object_t value, size_t* plength) 
{
    uint64_t hash = obj_hash(key);
    size_t index = (size_t)(hash & (uint64_t)(capacity - 1));

    ht_entry* ent;
    while ((ent = &entries[index])->key) {
        if (obj_cmp(key, ent->key))
            goto key_found;

        if (++index >= capacity) index = 0;
    }

    ent->key   = key;
key_found:
    ent->value = value;
}

static bool ht_expand(ht* table)
{
    size_t new_capacity = table->capacity * 2;

    size_t bytes = new_capacity * sizeof(ht_entry);
    ht_entry* new_entries = malloc(bytes);
    memset(new_entries, 0, bytes);

    for (size_t i = 0; i < table->capacity; i++) 
    {
        ht_entry entry = table->entries[i];
        if (entry.key)
            ht_set_entry(new_entries, new_capacity, entry.key, entry.value, NULL);
    }

    free(table->entries);
    table->entries  = new_entries;
    table->capacity = new_capacity;
}

void ht_set(ht* table, object_t key, object_t value)
{
    if (table->length >= table->capacity / 2)
        ht_expand(table);

    ht_set_entry(table->entries, table->capacity, key, value, &table->length);
}


/*
typedef struct {
    const char* key;  // current key
    void* value;      // current value

    // Don't use these fields directly.
    ht* _table;       // reference to hash table being iterated
    size_t _index;    // current index into ht._entries
} hti;


hti ht_iterator(ht* table) {
    hti it;
    it._table = table;
    it._index = 0;
    return it;
}

bool ht_next(hti* it) {
    // Loop till we've hit end of entries array.
    ht* table = it->_table;
    while (it->_index < table->capacity) {
        size_t i = it->_index;
        it->_index++;
        if (table->entries[i].key != NULL) {
            // Found next non-empty item, update iterator key and value.
            ht_entry entry = table->entries[i];
            it->key = entry.key;
            it->value = entry.value;
            return true;
        }
    }
    return false;
}

*/


#endif
