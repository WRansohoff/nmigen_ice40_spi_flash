from nmigen import *
from nmigen.back.pysim import *
from nmigen_boards.upduino_v2 import *
from nmigen_soc.wishbone import *
from nmigen_soc.memory import *

from helpers import *
from spi_rom import *

import sys

# Dummy LED class for testing.
class DummyLED():
  def __init__( self ):
    self.o = Signal( 1, reset = 0b0, name = 'led' )

# Test FSM for the SPI Flash module: Read values from RAM, and
# process a simple state machine based on them.
# xxxxxxxxx9: Turn red LED on.
# xxxxxxxxx1: Turn red LED off.
# xxxxxxxxxA: Turn green LED on.
# xxxxxxxxx2: Turn green LED on.
# xxxxxxxxx3: Turn blue LED off.
# xxxxxxxxxB: Turn blue LED off.
# xxxxxxxxx4: Delay for 'xxxxxxx' cycles.
# 0000000000: Jump back to word 0.
# FFFFFFFFFF: Jump back to word 0.
class SPI_TEST( Elaboratable ):
  def __init__( self, dat_offset, test_dat ):
    # SPI Flash Memory module (read-only)
    self.mem = SPI_ROM( dat_offset, dat_offset + 1024, test_dat )
    # Current memory pointer offset.
    self.pc = Signal( 32, reset = 0x00000000 )
    # Delay counter.
    self.dc = Signal( 28, reset = 0x0000000 )
  def elaborate( self, platform ):
    m = Module()
    m.submodules.mem = self.mem

    # LED resources.
    if platform is None:
      rled = DummyLED()
      gled = DummyLED()
      bled = DummyLED()
    else:
      rled = platform.request( 'led_r', 0 )
      gled = platform.request( 'led_g', 0 )
      bled = platform.request( 'led_b', 0 )

    # Set bus address to the 'program counter' value.
    m.d.comb += self.mem.adr.eq( self.pc )

    # State machine:
    # * 'FETCH':   Retrieve the next instruction from memory.
    # * 'PROCESS': Execute the current instruction.
    # * 'NEXT':    Let CS signal settle before moving on.
    with m.FSM():
      # 'FETCH' state: Get the next word from SPI Flash.
      with m.State( 'FETCH' ):
        # Pulse 'stb' and 'cyc' to start the bus transaction.
        m.d.sync += [
          self.mem.stb.eq( 1 ),
          self.mem.cyc.eq( 1 )
        ]
        # Proceed once 'ack' is asserted.
        with m.If( self.mem.ack == 1 ):
          # Reset the delay counter, and clear 'stb' / 'cyc' to end
          # the bus transaction. This also causes 'ack' to be cleared.
          m.d.sync += [
            self.dc.eq( 0 ),
            self.mem.stb.eq( 0 ),
            self.mem.cyc.eq( 0 )
          ]
          m.next = 'PROCESS'
        # Read is ongoing while 'ack' is not asserted.
        with m.Else():
          m.next = 'FETCH'
      # 'PROCESS' state: execute the retrieved instruction.
      with m.State( 'PROCESS' ):
        # Unless otherwise specified, add a word to the PC address
        # and proceed to the 'NEXT' state.
        m.d.sync += self.pc.eq( self.pc + 4 )
        m.next = 'NEXT'
        # If the word is 0 or -1, reset PC address to 0 instead of
        # incrementing it. 0xFFFFFFFF can indicate an error or
        # uninitialized SPI memory, so it's a good 'return' trigger.
        with m.If( ( self.mem.dat_r == 0x00000000 ) |
                   ( self.mem.dat_r == 0xFFFFFFFF ) ):
          m.d.sync += self.pc.eq( 0x00000000 )
        # If the 4 LSbits equal 0x4, delay for a number of cycles
        # indicated by the remaining 28 MSbits.
        with m.Elif( self.mem.dat_r[ :4 ] == 4 ):
          # If the delay has not finished, increment 'delay counter'
          # without changing the PC address, and return to the
          # 'PROCESS' state instead of moving on to 'NEXT'.
          with m.If( self.dc != ( self.mem.dat_r >> 4 ) ):
            m.d.sync += [
              self.dc.eq( self.dc + 1 ),
              self.pc.eq( self.pc )
            ]
            m.next = 'PROCESS'
        # If the 3 LSbits == 3, set the blue LED to the 4th bit.
        with m.Elif( self.mem.dat_r[ :3 ] == 3 ):
          m.d.sync += bled.o.eq( self.mem.dat_r[ 3 ] )
        # If the 3 LSbits == 2, set the green LED to the 4th bit.
        with m.Elif( self.mem.dat_r[ :3 ] == 2 ):
          m.d.sync += gled.o.eq( self.mem.dat_r[ 3 ] )
        # If the 3 LSbits == 1, set the red LED to the 4th bit.
        with m.Elif( self.mem.dat_r[ :3 ] == 1 ):
          m.d.sync += rled.o.eq( self.mem.dat_r[ 3 ] )
      # 'NEXT' state: Just a single-cycle delay to prepare the SPI
      # chip for a new transaction by allowing the 'CS' pin to settle.
      with m.State( 'NEXT' ):
        m.next = 'FETCH'

    # (End of SPI Flash test logic)
    return m

# 'main' method to build the test.
# Note: You can program an offset portion of the SPI Flash on an
# iCE40 board using the same open-source `iceprog` application which
# writes the bitstream. For a 2MByte offset: `iceprog -o 2M file.hex`
if __name__ == "__main__":
  # If the file was run with '-b', build for an 'Upduino' board
  # with the program located at a 2MByte offset.
  if ( len( sys.argv ) == 2 ) and ( sys.argv[ 1 ] == '-b' ):
    dut = SPI_TEST( 2 * 1024 * 1024, None )
    UpduinoV2Platform().build( dut )
  # If no arguments were passed in, simulate running the design with
  # a simple simulated test image at a 2MByte offset.
  else:
    dut = SPI_TEST( 2 * 1024 * 1024,
      [ R_ON, G_ON, DELAY( 10 ), R_OFF, DELAY( 5 ),
        G_OFF, B_ON, DELAY( 1 ), B_OFF, RET ] )
    with Simulator( dut, vcd_file = open( 'spi_test.vcd', 'w' ) ) as sim:
      # Simulate running for 5000 clock cycles.
      def proc():
        for i in range( 5000 ):
          yield Tick()
          yield Settle()
      sim.add_clock( 1e-6 )
      sim.add_sync_process( proc )
      sim.run()
