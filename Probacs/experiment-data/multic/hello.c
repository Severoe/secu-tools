#include "hello.h"
int hello(char* s){
    printf("Hello %s!\n", s);
    printf("Your name has %lu characters\n", strlen(s));
    return 0;
} 