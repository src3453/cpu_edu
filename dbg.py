# dbg.py - simple interactive debug monitor for SRC16.
# like old 6502 debugger, it shows register state, read memory, write memory and execute memory.

from cpu import CPU
from run import load_program

# command format:
# s: State - print register state.
# r[addr_start].[addr_end]: Read - show memory hexdump of specified memory area.
# w[addr].[value]: Write - write specific 8bit data to address.
# e[addr]: Execute - start execution from specified address.
# l[path].[addr]: Load specified binary file into start address.
# x: eXit - exit REPL.

cpu = CPU()

def notify_error(message):
    print(f"Error: {message}")

def print_registers(cpu):
    print("Current register state:")
    for i in range(16):
        if i == 14:
            print(f"R{i} (SP): {cpu.reg[i]:04X}")
        elif i == 15:
            print(f"R{i} (PC): {cpu.reg[i]:04X}")
        elif i == 0:
            print(f"R{i} (Zero): {cpu.reg[i]:04X}")
        else:
            print(f"R{i:2}: {cpu.reg[i]:04X}")
    print(f"FLAG: {cpu.flag:016b}") 

def print_hexdump(cpu, start, stop):
    print(f"Memory dump (0x{start:04X}~0x{stop:04X}):")
    for i in range(start, stop, 16):
        chunk = cpu.mem[i:i+16]
        print(f"{i:04X}: " + " ".join(f"{b:02X}" for b in chunk) + " " + "".join([chr(b) if 32 <= b <= 126 else '.' for b in chunk]))


def evaluate(input:str):
    if input == "":
        return
    command = input[0].lower()
    values = input[1:].split(".")


    match command:
        case "s":
            print_registers(cpu)
        case "r":
            if len(values) == 2:
                print_hexdump(cpu,int(values[0],16),int(values[1],16))
            else:
                notify_error("invalid operands")
        case "w":
            if len(values) == 2:
                cpu.mem[int(values[0],16)] = int(values[1],16)
                print(f"Wrote 0x{int(values[1],16):02X} to 0x{int(values[0],16):04X}")
                print_hexdump(cpu,int(values[0],16)//16*16,int(values[0],16)//16*16+15)
            else:
                notify_error("invalid operands")
        case "e":
            if len(values) == 1:
                cpu.pc = int(values[0],16)
                cpu.run()
            else:
                notify_error("invalid operands")
        case "l":
            if len(values) >= 2:
                path = ".".join(values[:-1])
                load_program(cpu, path, int(values[-1],16))
            else:
                notify_error("invalid operands")
        case "x":
            print("\nExiting, bye!")
            exit(0)
        case "h":
            print("""
        debugger help:
s: State - print register state.
r[addr_start].[addr_end]: Read - show memory hexdump of specified memory area.
w[addr].[value]: Write - write specific 8bit data to address.
e[addr]: Execute - start execution from specified address.
l[path].[addr]: Load specified binary file into start address.
x: eXit - exit REPL.
h: Help - show this help. (also "help" will work)
""")

        case _:
            notify_error("unknown command")



    
if __name__ == "__main__":
    print("SRC16 debug monitor")
    print("(c) 2026 src3453 MIT License.")
    while True:
        try:
            evaluate(input=input("> "))
        except KeyboardInterrupt:
            print("\nExiting, bye!")
            exit(0)