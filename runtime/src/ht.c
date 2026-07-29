#ifndef _G_HT
#define _G_HT

#include <stdint.h>
#include <stdbool.h>

#include <ht.h>
#include <util.h>

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



hti ht_iterator(ht* table) 
{
    return (hti) {
        .table = table,
        .index = -1,
    };
}

ht_entry* ht_next(hti* it) 
{
    if (it->index == -1) it->index = 0;

    ht* table = it->table;

    while (it->index < table->capacity) 
    {
        ht_entry* ent = &table->entries[it->index++];
        if (ent->key) return ent;
    }

    return NULL;
}

ht_entry* ht_count(hti* it)
    // assume keys are all KIND_INT. //or KINT_FLOAT
    // count to smallest key bigger than the current one.
    // in effect, count through the ht.
    // used to implemented arrays and strings.
{
    if (it->index == -1) it->index = INT64_MIN;
    ht* table = it->table;

    #define VALUE(ent) ((uint64_t)(ent)->key->data)

    // find smallest bigger than it->index
    ht_entry* best = NULL;
    for (size_t i = 0; i < table->capacity; i++)
    {
        ht_entry* ent = &table->entries[i];
        if (!ent->key) continue;

        if (ent->key->kind != KIND_INT) continue;
        int64_t value = VALUE(ent);

        // value must strictly be bigger.
        if (value <= it->index) continue;

        if (!best || VALUE(best) > value)
            best = ent;
    }

    if (best)
        it->index = VALUE(best);


    return best;    
}






#endif
