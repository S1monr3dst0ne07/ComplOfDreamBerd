#ifndef _H_UTIL
#define _H_UTIL

object_t util_create_string(const char* ptr);
void putstr(const char* msg);
void debug(const char* msg);
char* single_int_to_string(uint64_t x);

#endif
