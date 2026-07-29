

#include <platform.c>
#include <object.c>

void _print_numb(uint64_t x)
{
    static char buffer[64];
    char* iter = buffer + sizeof(buffer);

    #define write(c) (*(--iter)) = c

    write('\0');
    while (x)
    {
        write((x % 10) + '0');
        x = x / 10;
    }

    while (*iter) outchar(*iter++);
    outchar('\n');
}


void print(object_t obj)
{
    // refernces always goes out of scope
    obj_dec(obj);

    switch (obj->kind)
    {
        case KIND_INT:
            _print_numb((uint64_t)obj->data);
            break;
    }
    
}




