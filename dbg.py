# dbg.py - simple interactive debug monitor for SRC16.
# like old 6502 debugger, it shows register state, read memory, write memory and execute memory.

from cpu import CPU
import sys
from run import load_program

# command format:
# s: State - print register state.
# r[addr_start].[addr_end]: Read - show memory hexdump of specified memory area.
# w[addr].[value]: Write - write specific 8bit data to address.
# e[addr]: Execute - start execution from specified address.
# l[path].[addr]: Load specified binary file into start address.
# x: eXit - exit REPL.
 

def evaluate(input:str):
    command = input[0].lower()
    value = input[1:]
    
if __name__ == "__main__":
    pass