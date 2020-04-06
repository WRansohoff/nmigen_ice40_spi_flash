# iCE40 SPI Flash Access Test

This is a simple test of reading from the SPI Flash chip which is included on most `iCE40` FPGA boards. There is no on-chip re-writable non-volatile memory in an `iCE40`, but they do include hardware to automatically program themselves from commodity SPI Flash memories when they reset. So most multi-use development platforms include an external Flash chip, and they are usually sized to at least 2x the expected maximum size of a configuration bitstream.

The extra memory space is convenient if you want to experiment with writing a 'softcore' CPU, because you can store applications for your CPU to run in the leftover memory.

This design is a minimal test of reading data from an offset address in external Flash memory from an iCE40 chip. It targets an 'Upduino' board, which uses an `iCE40UP5K` in a QFN48 package with a Winbond `W25Q`-series Flash chip.

# Contents

* `spi_test.py`: The main application file, which contains a simple state machine. Depending on the values read out of the `SPI_ROM` module, it can toggle the board's 3 LEDs, delay for a given number of cycles, or jump back to address 0.

* `spi_rom.py`: The `SPI_ROM` module and associated testbench. This implements a simple Wishbone interface which reads four bytes from `adr + offset` when `cyc` and `stb` are asserted, and asserts `ack` when it is done until `stb` is de-asserted. The resulting word is stored in `dat_r` until the next read cycle.

# Prerequisites

This design uses `nMigen` to generate the synthesizable logic. You'll need to install the `nmigen`, `nmigen-boards`, and `nmigen-soc` Python libraries to build it:

* [nmigen](https://github.com/nmigen/nmigen/): The core high-level hardware description language. Or maybe it's an HDL description language?

* [nmigen-boards](https://github.com/nmigen/nmigen-boards/): Contains descriptions of the resources available to various development platforms, including the board used in this example.

* [nmigen-soc](https://github.com/nmigen/nmigen-soc/): Contains extra building blocks for assembling SoCs. This is where the Wishbone bus interface comes from.

The libraries are available from Pypi via `pip3`, but they are under very active development so you might want to install the most recent version from the repositories. I usually copy the package directly into `~/.local/lib/python3.[x]/site-packages/`. If you do that, you should copy the package directory (e.g. `nmigen-boards/nmigen_boards`), not the entire repository (e.g. `nmigen-boards`).

You'll also need the main components of the `Yosys` synthesis suite and the `icestorm` toolchain:

* [yosys](https://github.com/YosysHQ/yosys/): Open-source logic synthesizer.

* [nextpnr](https://github.com/YosysHQ/nextpnr): Open-source place-and-route tool.

* [icestorm](https://github.com/cliffordwolf/icestorm): Collection of open-source utilities which support `iCE40` development.

Each of those projects has its own comprehensvie build instructions.

# Usage

Once you've installed the prerequisites, you can build the test application by running:

    python3 spi_test.py -b

To program an `iCE40` board's SPI Flash, you can use the `iceprog` utility (which is more or less a general-purpose FT2232/SPI bridge):

    iceprog -o 2M spi_test.bin
    iceprog build/top.bin

The application reads from an offset of 2MBytes by default, and a basic `spi_test.bin` file is included to flash a few colors at different timings in a loop. If the LEDs cycle through purple / teal / yellow colors, the SPI module is working. If they don't, something done gone broke.

If you get an error from `iceprog` or see a Flash ID longer than four bytes, you can cancel the process and try again. You might also need to power-cycle the board if it repeatedly gets stuck on the "init..." step. Temporary problems can occur if the FPGA is using the SPI Flash chip when you try to start writing to it, but that shouldn't damage either chip permanently.

Even so, **BE CAREFUL!** It may be possible to brick a board which lacks jumpers for SPI access by mis-configuring the FPGA's SPI pins or failing to release the SPI resource. I don't think that should happen with this design, but it may be possible to get it into a state which is difficult to re-flash by not including a long 'delay' instruction somewhere in your test program. If that happens, the chip will almost always be busy reading from the chip, so you might have to re-try many times before catching it in a receptive state. Please simulate and double-check your designs before running them in hardware if you decide to build off of this example.

You can simulate the test application by running the `spi_test.py` file without the `-b` ("build") flag:

    python3 spi_test.py

The resulting waveform will be saved as, `spi_test.vcd`. The same goes for the `spi_rom.py` file, which also runs a few basic unit tests to simulate the process of reading a few words. Note that nMigen expects the `cs` signal to be inverted so that '1' means 'active'.

If you don't have a prefered waveform viewer, [GtkWave](http://gtkwave.sourceforge.net/) is Free.
