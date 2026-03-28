from cpu import CPU
import sys
import time

def load_program(cpu: CPU, filename: str, offset:int=0) -> None:
    with open(filename, "rb") as f:
        data = f.read()
        # cpu.mem is bytearray
        cpu.mem[offset:len(data)+offset] = data    

if __name__ == "__main__":
    cpu = CPU() # Create a CPU instance
    load_program(cpu, sys.argv[1]) # Load the assembled binary program into memory
    try:
        start_time = time.perf_counter()
        cpu.run() # Run the CPU until it halts
        end_time = time.perf_counter()
        cycles = cpu.cycle
        print(f"Program executed in {end_time - start_time:.6f} seconds.")
        print(f"Total cycles: {cycles} ({cycles / (end_time - start_time) / 1000:.2f} KIPS)")
    except KeyboardInterrupt:
        exit(0)
    print("\nCPU halted. Final register state:")
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
    print("Memory dump (first 256 bytes):")
    for i in range(0, 256, 16):
        chunk = cpu.mem[i:i+16]
        print(f"{i:04X}: " + " ".join(f"{b:02X}" for b in chunk) + " " + "".join([chr(b) if 32 <= b <= 126 else '.' for b in chunk]))
