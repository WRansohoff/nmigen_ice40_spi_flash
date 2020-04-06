# Convert a 32-bit word to little-endian byte format.
# 0x1234ABCD -> 0xCDAB3412
def LITTLE_END( v ):
  return ( ( ( v & 0x000000FF ) << 24 ) |
           ( ( v & 0x0000FF00 ) << 8  ) |
           ( ( v & 0x00FF0000 ) >> 8  ) |
           ( ( v & 0xFF000000 ) >> 24 ) )

# Helper methods / values for generating test ROM images.
R_ON  = LITTLE_END( 0x00000009 )
R_OFF = LITTLE_END( 0x00000001 )
G_ON  = LITTLE_END( 0x0000000A )
G_OFF = LITTLE_END( 0x00000002 )
B_ON  = LITTLE_END( 0x0000000B )
B_OFF = LITTLE_END( 0x00000003 )
RET   = LITTLE_END( 0x00000000 )
def DELAY( cycles ):
  return LITTLE_END( ( 0x4 | ( cycles << 4 ) ) & 0xFFFFFFFF )
