#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "Invalid arguments.\n");
        return EXIT_FAILURE;
    }

    char *str = argv[1];

    int l = 0;
    int h = strlen(str) - 1;
 
    while (h > l) {
        if (str[l++] != str[h--]) {
            printf("%s is not a palindrome.\n", str);
            return 0;
        }
    }
 
    printf("%s is a palindrome.\n", str);
    return 0;
}
