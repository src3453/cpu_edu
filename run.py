from cpu import CPU
import sys

def load_program(cpu: CPU, filename: str) -> None:
    with open(filename, "rb") as f:
        data = f.read()
        # cpu.mem is bytearray
        cpu.mem[:len(data)] = data    

if __name__ == "__main__":
    cpu = CPU() # Create a CPU instance
    load_program(cpu, sys.argv[1]) # Load the assembled binary program into memory
    cpu.run() # Run the CPU until it halts
    print(f"R1: {cpu.reg[1]}") # Should print R1: 42