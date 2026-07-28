
#include <stdint.h>
#include <stddef.h>

// warning: operating system stuff ahead.
// this file contains syscall bindings
// and a small user heap for linux.

// https://filippo.io/linux-syscall-table/
enum
{
    SYS_WRITE = 1,
    SYS_BRK   = 12,
};

#define SYS_CLOBBERS "rcx","r11","memory"
#define SYS_STDOUT 1


void outchar(char c)
{
    asm volatile (
        "syscall"
        : : "a"(SYS_WRITE), "D"(SYS_STDOUT), "S"(&c), "d"(1)
        : SYS_CLOBBERS
    );
}

uintptr_t brk(uintptr_t new)
{
    uintptr_t old;
    asm volatile (
        "syscall"
        : "=a"(old)
        : "a"(SYS_BRK), "D"(new)
        : SYS_CLOBBERS
    );
    return old;
}


// oh unix gods, bless this sbrk!
// may it never segfault, eventho it's ass.
void* sbrk(size_t inc)
{
    static uintptr_t curr = 0;

    // initialize to end-of-program address
    if (!curr) curr = brk(0);

    void* old = (void*)curr;
    curr += inc;
    brk(curr); // update break
    return old;
}

// original k&r malloc.
// no explicit alignment because who cares.
typedef struct _header_s
{
    struct _header_s* next;
    uint32_t size;
} header_t;

static header_t  base;
static header_t* freeptr = NULL; 

#define MIN_CORE_NUMB 1024

void free(void* base);
static header_t* morecore(size_t nu)
{
    if (nu < MIN_CORE_NUMB) nu = MIN_CORE_NUMB;

    header_t* head = sbrk(nu * sizeof(header_t));
    head->size = nu;

    void* base = head + 1;
    free(base); // merge into free list

    return freeptr;
}



void* malloc(size_t bytes)
{
    size_t units = (bytes + sizeof(header_t) - 1) / sizeof(header_t) + 1;

    if (freeptr == NULL)
    {
        base.next = freeptr = &base;
        base.size = 0;
    }

    header_t* curr; 
    header_t* prev = freeptr;

    for (curr = prev->next;; prev = curr, curr = curr->next) 
    {
        if (curr->size < units) goto not_big_enough;

        if (curr->size == units)
            // exact size, just unlink the block.
            prev->next = curr->next;
        else 
            // otherwise cut block.
        {
            //shrink old.
            curr->size -= units;
            //make new.
            curr += curr->size;   
            curr->size = units;  
        }

        // make sure free doesn't point to new block.
        freeptr = prev;
        return (void *)(curr+1);

not_big_enough:
        // still in free list, continue normally.
        if (curr != freeptr) continue; 

        // otherwise entire free list has been traversed.
        // need more core.
        curr = morecore(units);
    }
}


void free(void *base)
{

    header_t* head = (header_t*)base - 1;
    header_t* neigh;

    // is ptr in the bounds of block?
    #define BOUNDED(block, ptr) (block < ptr && ptr < block->next)
    #define SEMIBOUNDED(block, ptr) (block < ptr || ptr < block->next)
    #define LAST(block) (block >= block->next)

    #define AFTER(block) (block + block->size)

    // find neighbour of the block to be freed.
    for (neigh = freeptr; !BOUNDED(neigh, head); neigh = neigh->next)
        if (LAST(neigh) && SEMIBOUNDED(neigh, head))
            break;  /* freed block at start of end of arena */

    if (AFTER(head) == neigh->next) 
    {
        // coalesce into next
        head->size += neigh->next->size; 
        head->next  = neigh->next->next;
    } else
        head->next = neigh->next;

    if (AFTER(neigh) == head) 
    {
        // coalesce into prev
        neigh->size += head->size;
        neigh->next  = head->next;
    } else
        neigh->next = head;

    // make sure free doesn't point into changed blocks.
    freeptr = neigh;
}

