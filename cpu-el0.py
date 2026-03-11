""" 
# SRC16 (Scalable RISC 16-bit CPU) / EL0 Implementation

Educational fantasy CPU emulator, minimalistic and designed for learning purposes.
16-bit, big-endian, 16-bit address space, 16 general-purpose registers (R0-R15) and flag register, and a simple instruction set.
Register Usage:
    R14 is the stack pointer (SP), and R15 is the program counter (PC), R0 is the zero register (always reads as 0, writes are ignored).
    Register FLAG is the flag register (-----------IVCNZ), read-only.
    I: interrupt enable flag, V: overflow flag, C: carry (borrow) flag, N: negative flag, Z: zero flag.
    R1~R13 are general-purpose registers for arithmetic and data manipulation.
Instruction Format:
    The CPU is Register-based, with each instruction being 32 bits long (RISC-like), with the following format:
    R: [opcode (8 bits)][dest_reg (4 bits)][src1_reg (4 bits)][src2_reg (4 bits)][unused (12 bits)]
    I: [opcode (8 bits)][dest_reg (4 bits)][src1_reg (4 bits)][imm_val (16 bits)]
    each instruction consists of an opcode, two source registers, and a destination register or an immediate value.
Addressing Modes:
    The CPU supports direct register addressing, immediate values, and memory addressing through registers (e.g., [R1] for memory access).
    others can be added as needed, but the basic ones are sufficient for a simple emulator.
    Relative jumps uses signed values, allowing for jumps forward and backward within a range of -32768 to +32767 bytes from the current PC.
Stacks:
    The CPU has a simple stack mechanism, with the stack growing downwards in memory. 
    The stack pointer (SP) is initialized to the top of the stack area of memory (0xFE00) and is decremented on push and incremented on pop.
    Max stack depth is 256 bytes (128 entries), and stack overflow/underflow should be handled gracefully.
Memory Map:
    0x0000 - 0xFCFF: General-purpose memory for code and data
    0xFD00 - 0xFDFF: Stack area (256 bytes, 128 entries of 16-bit data)
    0xFE00 - 0xFEFF: Memory mapped I/O
    0xFF00 - 0xFFFF: interrupt vector (256 bytes, 128 entries of 16-bit address)
Memory Banking in EL2:
    0xFD00 - 0xFFFF will be fixed in bank 0, while 0x0000 - 0xFCFF can be switched between different memory banks to allow for more than 64KB of addressable memory.
Interrupts:
    The CPU uses an interrupt vector table starting at address 0xFF00.
    Each entry in the vector table is a 16-bit address pointing to an interrupt handler.

    Interrupt vector address formula:
        vector_address = 0xFF00 + (imm_val & 0x7F) * 2
        PC = MEM16[vector_address]

    INT instruction behavior:
        push FLAGS
        push PC
        clear I flag
        PC = MEM16[vector_address]

    IRET instruction behavior:
        pop PC
        pop FLAGS

    Hardware interrupts in EL2:
        EL2 introduces a WAIT instruction that puts the CPU in a not running state until an interrupt occurs.
        The CPU has 16 hardware interrupt lines (0-15), and when an interrupt is triggered, the corresponding bit in the interrupt status register is set.
        With IRQ_STATUS and IRQ_MASK registers, the CPU can check for pending interrupts and their priority.
        IRQ 0 is the highest priority and IRQ 15 is the lowest. When multiple interrupts are pending, the CPU will service the highest priority one first.
        IRQ interrupt vector will be calculated as INT 0x70 + IRQ number, allowing for up to 16 hardware interrupts with their own handlers. (e.g., IRQ 4 will trigger INT 0x74)
I/O:
    The CPU has a simple memory-mapped I/O system, with specific addresses reserved for input and output operations.  
    Note: LD, ST instructions in I/O address range (0xFE00-0xFEFF) will be treated as 8-bit I/O operations instead of 16-bit memory operations.
    0xFE00: UART I/O Register (write to output a byte, read to input a byte. virtual UART is connected to console)
    0xFE01: UART Status Register (bit 0: input ready, bit 1: output ready)
CPUID Instruction:
    The CPUID instruction (opcode 0xFD) can be used to query information about the CPU, such as vendor ID, supported features, and extension level.
    These values are returned in specific registers.
        R1: Vendor ID (currently 0x0000 only)
        R2: Extension Level (0 for EL0, 1 for EL1, etc.)
Instructions and Opcodes:
    The CPU has a concept called "Extension Level" (EL) which allows for future expansion of the instruction set.
    Extension level represents the set of instructions that the CPU supports, with higher levels including all instructions from lower levels plus additional ones.
    All Extension levels are backwards compatible, meaning that a CPU with a higher EL can run programs designed for lower ELs, but not vice versa.

    EL0 (Base Instructions, minimal set for basic operation):
        Load/Store:
        0x01: MOV dst_reg, src1_reg - Move data from src1_reg to dst_reg
        0x02: LD dst_reg, [src1_reg] - Load data from memory address formed by src1_reg into dst_reg
        0x03: ST [dst_reg], src1_reg - Store data from src1_reg into memory address formed by dst_reg
        0x04: LDI dst_reg, imm_val - Load immediate value into dst_reg

        ALU Operations:
        0x05: ADD dst_reg, src1_reg, src2_reg - Add src1_reg and src2_reg, store result in dst_reg
        0x06: SUB dst_reg, src1_reg, src2_reg - Subtract src2_reg from src1_reg, store result in dst_reg

        Branching:
        0x07: JMP imm_val - Jump to the specified address
        0x08: JZ imm_val - Jump to the specified address if zero flag is set
        0x09: JNZ imm_val - Jump to the specified address if zero flag is not set

        Stack Operations:
        0x0A: PUSH src_reg - Push data from src_reg onto the stack (SP decrements 2)
        0x0B: POP dst_reg - Pop data from the stack into dst_reg (SP increments 2)

        Subroutine Calls:
        0x0C: CALL imm_val - Call subroutine at the specified address (push return address onto stack and jump)
        0x0D: RET - Return from subroutine (pop return address from stack and jump)

        Interrupts:
        0x0E: INT imm_val - Trigger software interrupt
        0x0F: IRET - Return from interrupt
        0x10: EI - Enable interrupts (set I flag)
        0x11: DI - Disable interrupts (clear I flag)

        Special Instructions:
        0x00: NOP - No operation
        0xFD: CPUID - Return CPU information (e.g., vendor ID, extention level, supported features) in registers
        0xFE: RESET - Reset the CPU to initial state
        0xFF: HALT - Stop execution

    EL1 (Extended Instructions, for more complex operations useful for operating systems and advanced programming):
        Extended ALU Operations:
        0x12: AND dst_reg, src1_reg, src2_reg - Perform bitwise AND between src1_reg and src2_reg, store result in dst_reg
        0x13: OR dst_reg, src1_reg, src2_reg - Perform bitwise OR between src1_reg and src2_reg, store result in dst_reg
        0x14: XOR dst_reg, src1_reg, src2_reg - Perform bitwise XOR between src1_reg and src2_reg, store result in dst_reg
        0x15: SHL dst_reg, src1_reg, imm_val - Shift src1_reg left by imm_val bits, store result in dst_reg
        0x16: SHR dst_reg, src1_reg, imm_val - Shift src1_reg right by imm_val bits, store result in dst_reg
        0x17: CMP src1_reg, src2_reg - Compare src1_reg and src2_reg, update flags based on result (dst_reg is ignored)
        0x18: TEST src1_reg, src2_reg - Perform bitwise AND between src1_reg and src2_reg, update flags based on result (dst_reg is ignored)
        0x19: NOT dst_reg, src1_reg - Perform bitwise NOT on src1_reg, store result in dst_reg
        0x1A: INC dst_reg - Increment dst_reg by 1, store result in dst_reg (src1_reg, src2_reg are ignored)
        0x1B: DEC dst_reg - Decrement dst_reg by 1, store result in dst_reg (src1_reg, src2_reg are ignored)
        0x1C: NEG dst_reg, src1_reg - Negate src1_reg (two's complement), store result in dst_reg (src2_reg is ignored)

        Additional Stack Operations:
        0x1D: PUSHI imm_val - Push immediate value onto stack (SP increments 2)

        Additional Branching:
        0x1E: JR src_reg - Jump relative. Jump to address PC + (src_reg value) (useful for loops and function returns without needing an immediate value)
        0x1F: JZR src_reg - Jump relative if zero flag is set. Jump to address PC + (src_reg value) if zero flag is set
        0x20: JNZR src_reg - Jump relative if zero flag is not set. Jump to address PC + (src_reg value) if zero flag is not set
        0x21: JC src_reg - Jump if carry flag is set. Jump to address PC + (src_reg value) if carry flag is set
        0x22: JNC src_reg - Jump if carry flag is not set. Jump to address PC + (src_reg value) if carry flag is not set
        0x23: JRI imm_val - Jump relative immediate. Jump to address PC + imm_val

        Additional Load/Store Instructions:
        0x24: LEA dst_reg, src1_reg, imm_val - Load effective address. Calculate address by adding src1_reg and imm_val, store result in dst_reg (useful for accessing local variables on stack or array indexing)
        0x25: STI dst_reg, imm_val - Store immediate value to memory address formed by dst_reg. Calculate address from dst_reg, store imm_val at that address (useful for quickly storing constants to memory without needing an extra register to hold the value)
        0x26: LDB dst_reg, [src1_reg] - Load byte from memory address formed by src1_reg into dst_reg (similar to LD but for 8-bit data instead of 16-bit)
        0x27: STB [dst_reg], src1_reg - Store byte from src1_reg into memory address formed by dst_reg (similar to ST but for 8-bit data instead of 16-bit)
    
    EL2 (Hardware Interupt and Extended Memory Address, for supporting more than 64KB of memory in the future. Not implemented yet, but reserved for future expansion):
        BANK, SWITCH, and other instructions for managing multiple memory banks to effectively increase addressable memory space beyond 16 bits.
        WAIT, Timer and other hardware interrupt control instructions for more advanced interrupt handling capabilities.
        Extended Registers:
        Additional registers for managing memory banks, interrupt status, and other advanced features.
            IRQ_STATUS: Register to check pending hardware interrupts (bit 0-15 correspond to IRQ 0-15)
            IRQ_MASK: Register to enable/disable specific hardware interrupts (bit 0-15 correspond to IRQ 0-15)
            BANK_SEL: Register to select active memory bank for extended addressing 
            BANK_ATTR: Register to set attributes for memory banks (e.g., read/write permissions, cache settings, etc.). It will also be used to determine system memory size during CPUID instruction (e.g., 0 for 64KB, 1 for 128KB, etc.)

        Advanced Interrupt Control:
        0x28: WAIT - Wait for interrupt (puts CPU in not running state until an interrupt occurs)
        0x29: MASKIRQ imm_val - Mask (disable) specific IRQ line(s) based on imm_val bitmask
        0x2A: UNMASKIRQ imm_val - Unmask (enable) specific IRQ line(s) based on imm_val bitmask
        0x2B: ACKIRQ imm_val - Acknowledge specific IRQ line(s) based on imm_val bitmask (used to clear pending interrupt status after handling)
        0x2C: READIRQ dst_reg - Read IRQ status into dst_reg (bit 0-15 correspond to IRQ 0-15 pending status)

        Memory Bank Control:
        0x2D: BANK dst_reg, imm_val - Select memory bank based on imm_val and store current bank in dst_reg
        0x2E: SWITCH dst_reg, imm_val - Switch to memory bank specified by imm_val and store previous bank in dst_reg

    EL3 (Paging MMU and Virtual Memory, Privileged Instructions, for implementing virtual memory and more advanced OS features. Not implemented yet, but reserved for future expansion):
        In EL3, Supervisor mode instructions are introduced for managing virtual memory, page tables, and other MMU features.
        Page fault, Privilege violation, and other exceptions are introduced for handling various error conditions that can occur in a more complex operating system environment.

"""

import sys
import select

class CPUError(Exception):
    # Generic custom exception for CPU errors (e.g., invalid opcode, memory access violation)
    def __init__(self, message, pc, instr=None, cpu=None):
        super().__init__(message)
        self.pc = pc
        self.instr = instr
        self.cpu = cpu

    def __str__(self):
        pc_before = (self.pc - 4) & 0xFFFF
        txt = ""
        if self.instr is not None:
            txt += f"CPU Error at PC={pc_before:04X} (Instr={self.instr:08X}): {super().__str__()}"
        else:
            txt += f"CPU Error at PC={pc_before:04X}: {super().__str__()}"
        txt += "\nFinal register state:\n"
        for i in range(16):
            if i == 14:
                txt += f"R{i} (SP): {self.cpu.reg[i]:04X}\n"
            elif i == 15:
                txt += f"R{i} (PC): {self.cpu.reg[i]:04X}\n"
            elif i == 0:
                txt += f"R{i} (Zero): {self.cpu.reg[i]:04X}\n"
            else:
                txt += f"R{i:2}: {self.cpu.reg[i]:04X}\n"
        txt += f"FLAG: {self.cpu.flag:016b}"
        return txt

class InvalidOpcodeError(CPUError):
    # Exception for invalid opcode errors
    def __init__(self, opcode, pc, instr):
        super().__init__(f"Invalid opcode: {opcode:02X}", pc, instr)
        self.opcode = opcode

class StackOverflowError(CPUError):
    # Exception for stack overflow errors
    def __init__(self, pc):
        super().__init__("Stack overflow", pc)

class StackUnderflowError(CPUError):
    # Exception for stack underflow errors
    def __init__(self, pc):
        super().__init__("Stack underflow", pc)

class MemoryAccessError(CPUError):
    # Exception for invalid memory access errors
    def __init__(self, address, pc):
        super().__init__(f"Invalid memory access at address: {address:04X}", pc)
        self.address = address

# test
#raise InvalidOpcodeError(0xAB, 0x1234, 0xAB000000)

class CPU:
    # Main CPU class

    # Constants
    FLAG_Z = 1 << 0 # Zero flag
    FLAG_N = 1 << 1 # Negative flag
    FLAG_C = 1 << 2 # Carry flag
    FLAG_V = 1 << 3 # Overflow flag
    FLAG_I = 1 << 4 # Interrupt enable flag

    STACK_START = 0xFD00 # Start of stack area in memory
    STACK_SIZE = 0x100 # 256 bytes
    STACK_END = STACK_START + STACK_SIZE # Empty stack pointer
    STACK_ENTRIES = STACK_SIZE // 2 # 128 entries of 16-bit data

    CPU_EXTENSION_LEVEL = 0 # Current CPU Extension Level (EL0 = base instructions, EL1 = extended instructions, etc.)

    # Convenience properties for PC(R15) and SP(R14)
    @property
    def pc(self):
        return self.reg[15]

    @pc.setter
    def pc(self, val):
        self.reg[15] = val & 0xFFFF

    @property
    def sp(self):
        return self.reg[14]

    @sp.setter
    def sp(self, val):
        self.reg[14] = val & 0xFFFF

    # Main implementations
    def __init__(self):
        # Initialize CPU State
        self.mem = bytearray(0x10000)  # 64KB memory
        self.reset() # Set initial CPU state (registers, flags, PC, SP, etc.)

    def reset(self):
        # Reset CPU state to initial conditions (PC=0x0000, SP=End of stack area, clear registers and flags)
        self.reg = [0] * 16 # Clear all registers
        self.flag = 0 # clear flags
        self.running = True # reset running state to True
        self.pc = 0x0000 # Start execution from address 0 
        self.sp = self.STACK_END # Initialize stack pointer to top of stack area

    def mem8_read(self, addr):
        # Read 8-bit value from memory
        addr = addr & 0xFFFF # Ensure address wraps around 16-bit space
        return self.mem[addr]
    
    def mem8_write(self, addr, val):
        # Write 8-bit value to memory
        addr = addr & 0xFFFF # Ensure address wraps around 16-bit space
        self.mem[addr] = val & 0xFF

    def io8_read(self, addr):
        # Read 8-bit value from MMIO address
        match addr:
            case 0xFE00: # UART I/O register
                ch = sys.stdin.read(1)
                return ord(ch)
            case 0xFE01: # UART status register
                # Bit 0: input ready, Bit 1: output ready
                input_ready = 1 if select.select([sys.stdin], [], [], 0)[0] else 0
                output_ready = 1 # always ready to output
                return (output_ready << 1) | input_ready
            case _: # Invalid MMIO address
                return 0 # return 0 for reads from other MMIO addresses for now (could raise error or log warning if desired)

    def io8_write(self, addr, val):
        match addr:
            case 0xFE00: # UART I/O register
                print(chr(val & 0xFF), end='') # Output byte as character to console
            case _: # Invalid MMIO address
                None # ignore writes to other MMIO addresses for now (could raise error or log warning if desired)

    def read8(self, addr):
        # wrapper for switching I/O and normal memory access
        addr &= 0xFFFF
        if 0xFE00 <= addr <= 0xFEFF:
            return self.io8_read(addr) # Handle memory-mapped I/O read
        else:
            return self.mem8_read(addr) # Normal memory read

    def read16(self, addr):     
        hi = self.read8(addr)
        lo = self.read8((addr + 1) & 0xFFFF)

        return (hi << 8) | lo

    def read32(self, addr):
        hi = self.read16(addr)
        lo = self.read16((addr + 2) & 0xFFFF)

        return (hi << 16) | lo
    
    def write8(self, addr, val):
        # wrapper for switching I/O and normal memory access
        addr &= 0xFFFF
        if 0xFE00 <= addr <= 0xFEFF:
            self.io8_write(addr, val) # Handle memory-mapped I/O write
        else:
            self.mem8_write(addr, (val) & 0xFF) # Normal memory write

    def write16(self, addr, val):
        val &= 0xFFFF
        self.write8(addr, (val >> 8))
        self.write8(addr + 1, val)

    def write32(self, addr, val):
        val &= 0xFFFFFFFF
        self.write16(addr, (val >> 16))
        self.write16(addr + 2, val)

    def read(self, addr):
        # wrapper for ST, LD instructions to handle both 8-bit and 16-bit access based on address range
        if 0xFE00 <= addr <= 0xFEFF:
            return self.read8(addr) # I/O range uses 8-bit access
        else:
            return self.read16(addr) # Normal memory uses 16-bit access
    
    def write(self, addr, val):
        # wrapper for ST, LD instructions to handle both 8-bit and 16-bit access based on address range
        if 0xFE00 <= addr <= 0xFEFF:
            self.write8(addr, val) # I/O range uses 8-bit access
        else:
            self.write16(addr, val) # Normal memory uses 16-bit access

    def sign16(self, val):
        val &= 0xFFFF
        return val if val < 0x8000 else val - 0x10000

    # Stack operations
    def push(self, val):
        # Push 16-bit value onto stack
        if self.sp < self.STACK_START + 2: # Check for stack overflow (need at least 2 bytes free to push)
            raise StackOverflowError(self.pc, cpu=self)
        self.sp = (self.sp - 2) & 0xFFFF # Decrement SP by 2 (stack grows downwards)
        self.write16(self.sp, val) # Write value to stack at SP

    def pop(self):
        # Pop 16-bit value from stack
        if self.sp >= self.STACK_END: # Check for stack underflow (SP cannot go beyond end of stack area)
            raise StackUnderflowError(self.pc, cpu=self)
        value = self.read16(self.sp) # Read value from stack at SP
        self.sp = (self.sp + 2) & 0xFFFF # Increment SP by 2 (stack grows downwards)
        return value

    
    def set_flag(self, flag, cond):
        # Set or clear a specific flag based on condition
        if bool(cond): # ensure cond is treated as boolean
            self.flag |= flag
        else:
            self.flag &= ~flag

    def get_flag(self, flag):
        # Get the value of a specific flag (returns True if set, False if clear)
        return (self.flag & flag) != 0

    def update_flags_nz(self, val):
        # Update Zero and Negative flags based on value (used for ALU operations)
        val &= 0xFFFF # Ensure value is 16-bit
        # Update Zero and Negative flags based on value
        self.set_flag(self.FLAG_Z, val == 0)
        self.set_flag(self.FLAG_N, (val & 0x8000) != 0)

    def alu_add(self, a, b):
        # Perform addition and update flags
        a &= 0xFFFF
        b &= 0xFFFF
        result_full = a + b
        result = result_full & 0xFFFF

        self.update_flags_nz(result) # Update Zero and Negative flags
    
        self.set_flag(self.FLAG_C, result_full >= 0x10000) # Update Carry flag
        self.set_flag(self.FLAG_V, ((a ^ result) & (b ^ result) & 0x8000) != 0) # Update Overflow flag

        return result
    
    def alu_sub(self, a, b):
        # Perform subtraction and update flags
        a &= 0xFFFF
        b &= 0xFFFF
        result_full = a - b
        result = result_full & 0xFFFF

        self.update_flags_nz(result) # Update Zero and Negative flags

        self.set_flag(self.FLAG_C, a < b) # Update Carry flag (borrow)
        self.set_flag(self.FLAG_V, ((a ^ b) & (a ^ result) & 0x8000) != 0) # Update Overflow flag

        return result
    
    def fetch(self):
        # Fetch 32-bit instruction from memory at PC
        pc = self.pc
        instr = self.read32(pc) # Read 4 bytes from memory at PC
        self.pc = (self.pc + 4) & 0xFFFF # increment PC by 4 (size of instruction) and wrap around 16-bit address space
        return instr
    
    def decode(self, instr):
        # Decode instruction into opcode and operands
        opcode = (instr >> 24) & 0xFF
        dest_reg = (instr >> 20) & 0x0F
        src1_reg = (instr >> 16) & 0x0F
        src2_reg = (instr >> 12) & 0x0F
        imm_val = instr & 0xFFFF
        return opcode, dest_reg, src1_reg, src2_reg, imm_val
    
    def execute(self, opcode, dst_reg, src1_reg, src2_reg, imm_val, instr):
        # Execute instruction based on opcode
        match opcode:
            # EL0 Base Instructions
            case 0x00: # NOP
                pass
            # Load/Store Instructions
            case 0x01: # MOV dst_reg, src1_reg
                if dst_reg != 0: # ignore zero register
                    self.reg[dst_reg] = self.reg[src1_reg] & 0xFFFF
            case 0x02: # LD dst_reg, [src1_reg]
                if dst_reg != 0: # ignore zero register
                    addr = self.reg[src1_reg] & 0xFFFF
                    self.reg[dst_reg] = self.read(addr) & 0xFFFF
            case 0x03: # ST [dst_reg], src1_reg
                addr = self.reg[dst_reg] & 0xFFFF
                val = self.reg[src1_reg] & 0xFFFF
                self.write(addr, val)
            case 0x04: # LDI dst_reg, imm_val
                if dst_reg != 0: # ignore zero register
                    self.reg[dst_reg] = imm_val & 0xFFFF
            # ALU operations
            case 0x05: # ADD dst_reg, src1_reg, src2_reg
                result = self.alu_add(self.reg[src1_reg], self.reg[src2_reg])
                if dst_reg != 0: # ignore zero register (but still perform flags update)
                    self.reg[dst_reg] = result
            case 0x06: # SUB dst_reg, src1_reg, src2_reg
                result = self.alu_sub(self.reg[src1_reg], self.reg[src2_reg])
                if dst_reg != 0: # ignore zero register (but still perform flags update)
                    self.reg[dst_reg] = result
            # Branching
            case 0x07: # JMP imm_val
                self.pc = imm_val & 0xFFFF # jump to address
            case 0x08: # JZ imm_val
                if self.get_flag(self.FLAG_Z): # if zero flag is set
                    self.pc = imm_val & 0xFFFF # jump to address
            case 0x09: # JNZ imm_val
                if not self.get_flag(self.FLAG_Z): # if zero flag is not set
                    self.pc = imm_val & 0xFFFF # jump to address
            # Stack Operations
            case 0x0A: # PUSH src_reg
                self.push(self.reg[src1_reg])
            case 0x0B: # POP dst_reg
                val = self.pop()
                if dst_reg != 0: # ignore zero register (though still perform stack pop)
                    self.reg[dst_reg] = val
            # Subroutine Calls
            case 0x0C: # CALL imm_val
                self.push(self.pc) # push return address onto stack
                self.pc = imm_val & 0xFFFF # jump to subroutine
            case 0x0D: # RET
                self.pc = self.pop() # pop return address from stack and jump
            # Interrupts
            case 0x0E: # INT imm_val
                self.push(self.flag) # push FLAGS onto stack
                self.push(self.pc) # push PC onto stack
                self.set_flag(self.FLAG_I, False) # clear I flag to disable further interrupts
                vector_address = 0xFF00 + (imm_val & 0x7F) * 2 # calculate interrupt vector address
                self.pc = self.read16(vector_address) # load interrupt handler address from vector table and jump
            case 0x0F: # IRET
                self.pc = self.pop() # pop PC from stack and jump
                self.flag = self.pop() # pop FLAGS from stack
            case 0x10: # EI
                self.set_flag(self.FLAG_I, True) # set I flag to enable interrupts
            case 0x11: # DI
                self.set_flag(self.FLAG_I, False) # clear I flag to disable interrupts
            case 0xFD: # CPUID
                self.reg[1] = 0x0000 # Vendor ID (currently 0x0000 only)
                self.reg[2] = self.CPU_EXTENSION_LEVEL # Extension Level (0 for EL0, 1 for EL1, etc.)
            case 0xFE: # RESET
                self.reset() # reset CPU state
            case 0xFF: # HALT
                self.running = False # stop execution
            case _: # invalid opcode
                raise CPUError(f"Invalid opcode: {opcode:02X}",self.pc, instr, self)

    def step(self):
        # each CPU step
        instr = self.fetch() # Fetch instruction at PC
        opcode, dest_reg, src1_reg, src2_reg, imm_val = self.decode(instr) # Decode instruction
        self.execute(opcode, dest_reg, src1_reg, src2_reg, imm_val, instr) # Execute instruction
        self.reg[0] = 0 # R0 is always zero
    
    def run(self):
        # actually run CPU while running
        while self.running:
            self.step()

if __name__ == "__main__":
    cpu = CPU()
    # Example: Load immediate value 42 into R1, then halt
    cpu.write32(0x0000, (0x04 << 24) | (1 << 20) | 42) # LDI R1, 42
    cpu.write32(0x0004, (0xFF << 24)) # HALT
    cpu.run()
    print(f"R1: {cpu.reg[1]}") # Should print R1: 42