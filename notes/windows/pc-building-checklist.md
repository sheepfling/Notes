# PC-building and upgrade checklist

> Type: reference
> Status: needs-review
> Updated: 2026-08-01
> Tags: hardware, pc-building, windows

This is a distilled version of a miscellaneous hardware bookmark list. It keeps the durable questions to ask during a
build or upgrade and drops the original short-video URLs, which were not a stable or validated source of record.

## Before buying parts

- Treat M.2 as a physical form factor, not a protocol. An M.2 drive may use SATA or NVMe; confirm what the motherboard
  slot supports and whether using it disables a SATA port or PCIe slot.
- Check motherboard form factor, CPU socket, chipset, number of memory channels, PCIe slot layout, M.2 slots, rear I/O,
  and firmware support before choosing a case or expansion card.
- Confirm the memory generation and capacity are supported by both the board and CPU. A matched kit is easier to
  validate than a mixture of kits, even when the headline specifications match.
- Size the power supply for the complete system, including transient GPU demand and connector requirements. An
  efficiency badge is not a complete quality or reliability rating.
- Check monitor resolution, refresh rate, input type, cable capability, and adaptive-sync support as one system rather
  than choosing a cable at the end.

## Assembly

- Remove protective films and shipping covers before operation, including any film on an M.2 heatsink or cooler contact
  surface.
- Install a two-module memory kit in the slots recommended by the motherboard manual, commonly the second slot in each
  channel, but do not assume the pattern for every board.
- Seat the graphics card in the board's primary full-length slot unless the manual says otherwise. Fully seat its power
  connector and avoid sharp bends at high-current connectors.
- Use the appropriate CPU cooler mount, apply a sensible amount of thermal compound, and confirm that the pump or fan
  headers are connected before the first sustained load.
- Aim for neutral or slightly positive case pressure with a deliberate intake/exhaust path. Fan count alone does not
  determine cooling; free-air flow and static pressure serve different jobs.
- Leave service slack in cables, label unfamiliar connections, and keep intake filters accessible.

## First boot and no-display checks

1. Observe POST indicators, speaker codes, or the motherboard's diagnostic display.
2. Confirm the monitor is connected to the discrete GPU when one is installed. The motherboard video connector may only
   work when the CPU provides integrated graphics.
3. Try a known-good cable and input, then reseat the GPU and memory with power removed.
4. Start with one memory module in the manual's recommended slot if the system will not POST.
5. Enter firmware setup, load stable defaults, and postpone XMP/EXPO until the baseline is proven.
6. Change one component or setting at a time and record what changed.

## Drivers and operating-system variables

- When replacing a graphics card, install the intended driver for the new card. A display-driver cleanup utility can be
  useful for a controlled driver transition, but create a recovery path and avoid treating every visual glitch as a
  driver problem.
- If a monitor appears as an unwanted audio output, disable that endpoint only after confirming the desired audio path.
  Audio-enhancement settings can add latency, but the effect depends on the driver and device.
- USB ports may differ in speed, charging behavior, and controller. Check the board manual instead of inferring
  capability from color alone.

## Performance notes

- Frame generation can improve perceived smoothness in supported single-player workloads while adding a latency
  tradeoff; competitive settings should be evaluated separately.
- G-SYNC, FreeSync, and related adaptive-sync modes coordinate display refresh with frame delivery. Match the monitor,
  GPU, cable, driver, and in-game settings before judging the result.
- More monitors, higher refresh rates, and higher resolutions multiply bandwidth and GPU workload. Check the GPU's
  simultaneous-output limits and cable standards.

## Evidence and recovery

Keep part numbers, firmware version, memory slot arrangement, profile settings, and error symptoms in the same
troubleshooting record. If an upgrade causes crashes, return to the last known-good configuration and
follow [the RAM upgrade troubleshooting note](ram-upgrade-bluescreen.md) before adding more changes.

This checklist is a starting point, not a substitute for the specific motherboard, CPU, GPU, PSU, and cooler manuals.
The original bookmark dump remains outside the repository because its links and claims were not individually validated.
