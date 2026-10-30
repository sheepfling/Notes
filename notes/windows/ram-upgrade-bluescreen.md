# Troubleshooting blue screens after a RAM upgrade

> Type: troubleshooting  
> Status: needs-review  
> Updated: 2026-08-01

This note distills an incident where a system became unstable after moving from a single,
known-good DDR5 configuration to mixed-capacity modules. The original material included raw
crash-dump output; the raw dump, file names, memory addresses, usernames, and machine-specific
build details are intentionally not retained here.

## Initial observation

The instability began after changing the memory configuration. Reliability Monitor recorded
hardware-related and blue-screen events, including `WHEA` and kernel `bugcheck` reports. A debugger
trace reached kernel heap-management code, but a kernel location alone does not prove that Windows
itself is the root cause: bad RAM, an unstable memory controller, timings, firmware, or another
driver can corrupt memory before the eventual crash.

The strongest evidence was behavioral: removing the added/mixed modules and returning to a simpler
configuration stopped the blue screens. That makes the memory configuration the leading hypothesis,
not a mathematically conclusive diagnosis.

## Safe isolation procedure

1. Shut down fully and reseat the modules. Follow the motherboard manual for the recommended slot
   pair; dual-channel systems commonly use a specific pair rather than adjacent slots.
2. Return to one known-good kit or module configuration. Do not mix kits merely because their
   capacity, advertised speed, and DDR generation match.
3. Enter firmware setup and load stable defaults. Disable XMP/EXPO or other memory overclocking
   while establishing a baseline.
4. Boot the baseline configuration and run the workload that previously failed. Record whether
   the system remains stable.
5. Test modules individually and in the motherboard's recommended slots. If a failure follows one
   module, suspect the module; if it follows one slot or channel, investigate the board, socket,
   or memory controller.
6. Run a memory test long enough to expose intermittent failures. Windows Memory Diagnostic is a
   useful first check; a bootable, more thorough memory tester can provide a second opinion.
7. Only after the baseline is stable, add one change at a time. Re-enable XMP/EXPO last, and keep
   the configuration within the board and CPU vendor's supported memory population guidance.

## What the supporting checks can and cannot show

### Reliability Monitor and Event Viewer

Use them to establish timing and recurrence, then record the `bugcheck` code and whether the event
started immediately after the hardware change. They are useful for correlation, not proof of the
failed component.

### WinDbg

Open a dump with matching symbols and start with:

```text
!analyze -v
kv
lm
```

If symbol loading is slow or incomplete, configure the Microsoft symbol path and reload symbols.
Capture the `bugcheck` code, probable module, stack, and dump type in a separate incident record,
but redact addresses, user paths, hostnames, and other identifying values before putting that
record in shared notes.

### Disk checks

`chkdsk /scan` can rule out some filesystem problems, but a clean filesystem scan does not validate
RAM, the memory controller, or firmware. Keep storage diagnostics separate from memory diagnostics.

### Recovery or boot errors

A recovery-screen error during a memory investigation is a separate symptom. Photograph or record
the exact code, determine whether it repeats on the baseline configuration, and avoid treating one
boot failure as confirmation of the RAM hypothesis.

## Practical conclusion

When a machine is stable with one supported kit and unstable with mixed modules, leave the stable
configuration in place while checking the board's compatibility list, firmware notes, module
part numbers, and supported population rules. Do not immediately restore an overclocking profile
just because the system appears stable for one session. Change one variable at a time and keep a
short record of module arrangement, firmware settings, test duration, and observed failures.

This is a troubleshooting method, not a component diagnosis. Replace a module or board only after
isolating the failure as far as practical.
