#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void palindrome(const char *str)
{
    int l = 0;
    int h = strlen(str) - 1;
 
    while (h > l) {
        if (str[l++] != str[h--]) {
            printf("%s is not a palindrome.\n", str);
            return;
        }
    }
 
    printf("%s is a palindrome.\n", str);
}


int main(int argc, char *argv[])
{
    if (argc > 2) {
        fprintf(stderr, "Invalid arguments.\n");
        return EXIT_FAILURE;
    }

    if (argc == 2) {
        palindrome(argv[1]);
        return EXIT_SUCCESS;
    } 


    char *line = NULL;
    size_t len = 0;
    while (getline(&line, &len, stdin) != -1) {
        line[strlen(line) - 1] = '\0';
        if (strlen(line) > 0)
            palindrome(line);
    }

    return EXIT_SUCCESS;
}
