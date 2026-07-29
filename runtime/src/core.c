
#include <stdint.h>
#include <stddef.h>
// core c functions.
// why are these not built in? 


void memset(void* ptr, uint8_t val, size_t count)
{
    uint8_t* _ptr = (uint8_t*)ptr;
    for (size_t i = 0; i < count; i++)
        *(_ptr++) = val;
}

void memcpy(void* dst, void* src, size_t count)
{
    uint8_t* _dst = (uint8_t*)dst;
    uint8_t* _src = (uint8_t*)src;

    for (size_t i = 0; i < count; i++)
        *(_dst++) = *(_src++);
}






