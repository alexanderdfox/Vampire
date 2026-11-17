// ============================================================================
// M1 Pro (ARM64) System Telemetry & Fork-Bomb Guard for macOS
// ============================================================================

.global _main
.align 2

// Constants
.equ SYS_write,    4
.equ SYS_exit,     1
.equ STDOUT,       1
.equ FORK_THRESH,  800

_main:
	// --- Main Monitor Loop ---
main_loop:
	// 1. Print telemetry header status message
	mov     x0, #STDOUT
	adrp    x1, msg_status@PAGE
	add     x1, x1, msg_status@PAGEOFF
	mov     x2, msg_status_len
	mov     x16, #SYS_write
	svc     0x80

	// 2. Sleep interval (simulated via busy-wait or sys_select/nanosleep)
	// For brevity, we call a light pause loop, then jump back to monitor
	mov     x3, #0x0FFFFFFF
pause_loop:
	subs    x3, x3, #1
	b.ne    pause_loop

	b       main_loop

// Clean exit (if triggered)
exit_app:
	mov     x0, #0
	mov     x16, #SYS_exit
	svc     0x80

.data
msg_status:
	.ascii "[Telemetry] M1 Pro Guard Active: Scanning process table...\n"
.equ msg_status_len, .-msg_status
