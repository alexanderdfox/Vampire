#include <unistd.h>
#include <signal.h>

int main() {
    while (1) {
        if (fork() == 0) {
            execlp("./vampire",  NULL);
        }
        kill(getpid(), SIGKILL);
    }
}
