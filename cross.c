#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32)
#include <windows.h>
#include <tlhelp32.h>
#include <process.h>
#define getpid _getpid
#define sleep(s) Sleep((s) * 1000)
#else
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#if defined(__APPLE__)
#include <libproc.h>
#elif defined(__linux__)
#include <dirent.h>
#include <ctype.h>
#endif
#endif

#define FORK_THRESHOLD 800
#define MAX_PROCS 4096

typedef struct {
    int pid;
    char name[256];
} ProcessInfo;

// Platform-native process enumeration (No external `ps` command needed)
int get_all_processes(ProcessInfo *procs, int max_procs) {
    int count = 0;

#if defined(_WIN32)
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return 0;

    PROCESSENTRY32 entry;
    entry.dwSize = sizeof(entry);

    if (Process32First(snapshot, &entry)) {
        do {
            if (count < max_procs) {
                procs[count].pid = (int)entry.th32ProcessID;
                // Wide char to multi-byte conversion for process name
                snprintf(procs[count].name, sizeof(procs[count].name), "%ls", entry.szExeFile);
                count++;
            }
        } while (Process32Next(snapshot, &entry));
    }
    CloseHandle(snapshot);

#elif defined(__APPLE__)
    pid_t pids[MAX_PROCS];
    int num_pids = proc_listpids(PROC_ALL_PIDS, 0, pids, sizeof(pids));
    num_pids /= sizeof(pid_t);

    for (int i = 0; i < num_pids && count < max_procs; i++) {
        if (pids[i] == 0) continue;
        char name[256];
        if (proc_name(pids[i], name, sizeof(name)) > 0) {
            procs[count].pid = (int)pids[i];
            strncpy(procs[count].name, name, sizeof(procs[count].name));
            count++;
        }
    }

#elif defined(__linux__)
    DIR *dir = opendir("/proc");
    if (!dir) return 0;

    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL && count < max_procs) {
        // Check if directory name is a number (PID)
        int is_pid = 1;
        for (int i = 0; entry->d_name[i] != '\0'; i++) {
            if (!isdigit(entry->d_name[i])) {
                is_pid = 0;
                break;
            }
        }

        if (is_pid) {
            int pid = atoi(entry->d_name);
            char comm_path[512];
            snprintf(comm_path, sizeof(comm_path), "/proc/%d/comm", pid);
            
            FILE *f = fopen(comm_path, "r");
            if (f) {
                char name[256];
                if (fgets(name, sizeof(name), f)) {
                    name[strcspn(name, "\n")] = 0; // Remove newline
                    procs[count].pid = pid;
                    strncpy(procs[count].name, name, sizeof(procs[count].name));
                    count++;
                }
                fclose(f);
            }
        }
    }
    closedir(dir);
#endif

    return count;
}

void terminate_process(int pid) {
#if defined(_WIN32)
    HANDLE h = OpenProcess(PROCESS_TERMINATE, FALSE, pid);
    if (h) {
        TerminateProcess(h, 1);
        CloseHandle(h);
    }
#else
    kill((pid_t)pid, SIGKILL);
#endif
}

void monitor_and_mitigate() {
    int my_pid = (int)getpid();
    ProcessInfo procs[MAX_PROCS];
    int total_procs = get_all_processes(procs, MAX_PROCS);

    printf("[Telemetry] Total Active Processes: %d\n", total_procs);

    if (total_procs > FORK_THRESHOLD) {
        printf("\n[!] 🚨 CRITICAL: FORK BOMB DETECTED (%d processes)!\n", total_procs);

        // Count occurrences of each process name to find the rogue culprit
        char rogue_name[256] = "";
        int max_count = 0;

        for (int i = 0; i < total_procs; i++) {
            int current_count = 0;
            for (int j = 0; j < total_procs; j++) {
                if (strcmp(procs[i].name, procs[j].name) == 0) {
                    current_count++;
                }
            }
            if (current_count > max_count) {
                max_count = current_count;
                strncpy(rogue_name, procs[i].name, sizeof(rogue_name));
            }
        }

        if (max_count >= 50) {
            printf("[!] Purging %d instances of runaway process '%s'...\n", max_count, rogue_name);
            for (int i = 0; i < total_procs; i++) {
                if (strcmp(procs[i].name, rogue_name) == 0 && procs[i].pid > 1 && procs[i].pid != my_pid) {
                    printf(" -> Terminating PID %d (%s)\n", procs[i].pid, procs[i].name);
                    terminate_process(procs[i].pid);
                }
            }
        }
    } else {
        printf("[Status] Secure: Fork Bomb Guard Active (Zero threats detected)\n");
    }
    printf("--------------------------------------------------\n");
}

int main() {
    printf("==================================================\n");
    printf("   Cross-Platform C Telemetry & Fork-Bomb Guard   \n");
    printf("==================================================\n");
    printf("My PID: %d\n\n", (int)getpid());

    while (1) {
        monitor_and_mitigate();
        sleep(2);
    }

    return 0;
}
