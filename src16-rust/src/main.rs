// SRC16 - Scalable RISC 16-bit CPU Emulator
// Rust implementation of the SRC16 CPU emulator (originally written in Python), designed for educational purposes.

/*
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
*/

const FLAG_Z: u16 = 1 << 0; // Zero flag
const FLAG_N: u16 = 1 << 1; // Negative flag
const FLAG_C: u16 = 1 << 2; // Carry flag
const FLAG_V: u16 = 1 << 3; // Overflow flag
const FLAG_I: u16 = 1 << 4; // Interrupt enable flag
const STACK_START: u16 = 0xFD00; // Start of stack area in memory
const STACK_SIZE: u16 = 0x100; // 256 bytes
const STACK_END: u16 = STACK_START + STACK_SIZE; // Empty stack pointer
const STACK_ENTRIES: u16 = STACK_SIZE / 2; // 128 entries of 16-bit data
const CPU_EXTENSION_LEVEL: u8 = 1; // Current CPU Extension Level (EL0 = base instructions, EL1 = extended instructions, etc.)
const REG_PC: usize = 15; // Program Counter register index
const REG_SP: usize = 14; // Stack Pointer register index
const REG_ZERO: usize = 0; // Zero register index (always reads as 0

struct CPU {
    reg: [u16; 16], // R0-R15 general-purpose registers 
    flags: u16,          // Flag register
    mem: [u8; 65536], // 16-bit address space (64KB)
    running: bool,     // CPU running state
}

impl CPU {
    fn new() -> Self {
        let mut cpu = CPU {
            reg: [0; 16],
            flags: 0,
            mem: [0; 65536],
            running: false,
        };
        cpu.reset(); // Initialize CPU state
        cpu // return the initialized CPU instance
    }

    fn reset(&mut self) {
        self.reg = [0; 16];
        self.flags = 0;
        self.mem = [0; 65536];
        self.reg[REG_SP] = STACK_END; // Initialize stack pointer to top of stack
        self.running = true;
    }

    fn mem8_read(&self, addr: u16) -> u8 {
        self.mem[addr as usize] // return the byte at the specified address
    }

    fn io8_read(&self, addr: u16) -> u8 {
        // Placeholder implementation - replace with actual I/O read logic
        match addr {
            0xFE00 => {
                // UART I/O Register - read a byte from input (virtual UART connected to console)
                0 // return 0 for now, you can implement actual input reading logic if needed
            }
            0xFE01 => {
                // UART Status Register - bit 0: input ready, bit 1: output ready
                0b00000011 // indicate both input and output are ready for now
            }
            _ => {
                0 // return 0 for other I/O addresses, or implement additional behavior as needed
            }
        }
    }

    fn mem8_write(&mut self, addr: u16, value: u8) {
        self.mem[addr as usize] = value; // write the byte to the specified address in memory
    }

    fn io8_write(&mut self, addr: u16, value: u8) {
        match addr {
            0xFE00 => {
                // UART I/O Register - write to output a byte (virtual UART connected to console)
                print!("{}", value as char); // output the byte as a character to the console
            }
            0xFE01 => {
                // UART Status Register - read-only, writing has no effect
                // You can choose to ignore writes or log a warning if needed
            }
            _ => {
            // For other I/O addresses, you can implement additional behavior as needed
            }
        }
    }

    fn read8(&self, addr: u16) -> u8 {
        if addr >= 0xFE00 && addr <= 0xFE01 {
            self.io8_read(addr) // treat as I/O read for addresses in the I/O range
        } else {
            self.mem8_read(addr) // treat as normal memory read for addresses outside the I/O range
        }
    }

    fn write8(&mut self, addr: u16, value: u8) {
        if addr >= 0xFE00 && addr <= 0xFEFF {
            self.io8_write(addr, value) // treat as I/O write for addresses in the I/O range
        } else {
            self.mem8_write(addr, value) // treat as normal memory write for addresses outside the I/O range
        }
    }

    fn read16(&self, addr: u16) -> u16 {
        let high = self.read8(addr) as u16;
        let low = self.read8(addr + 1) as u16;
        (high << 8) | low // return the combined 16-bit value (big-endian)
    }

    fn write16(&mut self, addr: u16, value: u16) {
        let high = (value >> 8) as u8;
        let low = (value & 0xFF) as u8;
        self.write8(addr, high);
        self.write8(addr + 1, low);
    }

    fn read32(&self, addr: u16) -> u32 {
        let high = self.read16(addr) as u32;
        let low = self.read16(addr + 2) as u32;
        (high << 16) | low // return the combined 32-bit value (big-endian)
    }

    fn write32(&mut self, addr: u16, value: u32) {
        let high = (value >> 16) as u16;
        let low = (value & 0xFFFF) as u16;
        self.write16(addr, high);
        self.write16(addr + 2, low);
    }

    fn read(&self, addr: u16) -> u16 {
        if addr >= 0xFE00 && addr <= 0xFEFF {
            self.read8(addr) as u16 // treat as I/O read for addresses in the I/O range, return as u16 for consistency
        } else {
            self.read16(addr) as u16 // treat as normal memory read for addresses outside the I/O range, return as u16 for consistency
        }
    }

    fn write(&mut self, addr: u16, value: u16) {
        if addr >= 0xFE00 && addr <= 0xFEFF {
            self.write8(addr, (value & 0xFF) as u8) // treat as I/O write for addresses in the I/O range, only write the lower 8 bits
        } else {
            self.write16(addr, value) // treat as normal memory write for addresses outside the I/O range
        }
    }

    fn push(&mut self, value: u16) {
        self.reg[REG_SP] = self.reg[REG_SP].wrapping_sub(2); // decrement stack pointer by 2 (stack grows downwards)
        self.write(self.reg[REG_SP], value); // write the value to the stack
    }

    fn pop(&mut self) -> u16 {
        let value = self.read(self.reg[REG_SP]); // read the value from the stack
        self.reg[REG_SP] = self.reg[REG_SP].wrapping_add(2); // increment stack pointer by 2
        value // return the popped value
    }   

    fn set_flag(&mut self, flag: u16, condition: bool) {
        if condition {
            self.flags |= flag; // set the specified flag bit
        } else {
            self.flags &= !flag; // clear the specified flag bit
        }
    }

    fn get_flag(&self, flag: u16) -> bool {
        (self.flags & flag) != 0 // return true if the specified flag bit is set, false otherwise
    }

    fn update_flags_nz(&mut self, result: u16) {
        self.set_flag(FLAG_Z, result == 0); // set zero flag if result is zero
        self.set_flag(FLAG_N, (result & 0x8000) != 0); // set negative flag if the most significant bit of the result is 1 (indicating a negative value in two's complement)
    }

    // ALU operations

    fn alu_add(&mut self, dest: usize, src1: usize, src2: usize) {
        let a = self.reg[src1] as u32;
        let b = self.reg[src2] as u32;
        let result = a + b;
        self.reg[dest] = result as u16; // store the lower 16 bits of the result in the destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
        self.set_flag(FLAG_C, result > 0xFFFF); // set carry flag if there was an overflow beyond 16 bits
        self.set_flag(FLAG_V, ((a ^ b) & 0x8000 == 0) && ((a ^ result) & 0x8000 != 0)); // set overflow flag if there was a signed overflow
    }

    fn alu_sub(&mut self, dest: usize, src1: usize, src2: usize) {
        let a = self.reg[src1] as u32;
        let b = self.reg[src2] as u32;
        let result = a.wrapping_sub(b);
        self.reg[dest] = result as u16; // store the lower 16 bits of the result in the destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
        self.set_flag(FLAG_C, a >= b); // set carry flag if there was no borrow (i.e., if a is greater than or equal to b)
        self.set_flag(FLAG_V, ((a ^ b) & 0x8000 != 0) && ((a ^ result) & 0x8000 != 0)); // set overflow flag if there was a signed overflow
    }

    fn alu_and(&mut self, dest: usize, src1: usize, src2: usize) {
        self.reg[dest] = self.reg[src1] & self.reg[src2]; // perform bitwise AND and store result in destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
    }

    fn alu_or(&mut self, dest: usize, src1: usize, src2: usize) {
        self.reg[dest] = self.reg[src1] | self.reg[src2]; // perform bitwise OR and store result in destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
    }

    fn alu_xor(&mut self, dest: usize, src1: usize, src2: usize) {
        self.reg[dest] = self.reg[src1] ^ self.reg[src2]; // perform bitwise XOR and store result in destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
    }

    fn alu_cmp(&mut self, src1: usize, src2: usize) {
        // using alu_sub to perform the comparison and set flags accordingly, but discarding the result
        let a = self.reg[src1] as u32;
        let b = self.reg[src2] as u32;
        let result = a.wrapping_sub(b);
        self.update_flags_nz(result as u16); // update zero and negative flags based on the result
        self.set_flag(FLAG_C, a >= b); // set carry flag if there was no borrow (i.e., if a is greater than or equal to b)
        self.set_flag(FLAG_V, ((a ^ b) & 0x8000 != 0) && ((a ^ result) & 0x8000 != 0)); // set overflow flag if there was a signed overflow     
    }

    fn alu_test(&mut self, src1: usize, src2: usize) {
        let result = self.reg[src1] & self.reg[src2]; // perform bitwise AND for TEST instruction
        self.update_flags_nz(result); // update zero and negative flags based on the result
    }

    fn alu_shl(&mut self, dest: usize, src1: usize, imm: u16) {
        let value = self.reg[src1] as u32;
        let shift_amount = (imm & 0xF) as u32; // limit shift amount to 0-15
        let result = value << shift_amount;
        self.reg[dest] = result as u16; // store the lower 16 bits of the result in the destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
        self.set_flag(FLAG_C, (value << (shift_amount - 1)) & 0x8000 != 0); // set carry flag based on the last bit shifted out
    }

    fn alu_shr(&mut self, dest: usize, src1: usize, imm: u16) {
        let value = self.reg[src1] as u32;
        let shift_amount = (imm & 0xF) as u32; // limit shift amount to 0-15
        let result = value >> shift_amount;
        self.reg[dest] = result as u16; // store the lower 16 bits of the result in the destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
        self.set_flag(FLAG_C, (value >> (shift_amount - 1)) & 0x1 != 0); // set carry flag based on the last bit shifted out
    }

    fn alu_not(&mut self, dest: usize, src1: usize) {
        self.reg[dest] = !self.reg[src1]; // perform bitwise NOT and store result in destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
    }

    fn alu_neg(&mut self, dest: usize, src1: usize) {
        let value = self.reg[src1] as u32;
        let result = (!value).wrapping_add(1); // perform two's complement negation
        self.reg[dest] = result as u16; // store the lower 16 bits of the result in the destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
        self.set_flag(FLAG_C, value != 0); // set carry flag if there was a borrow (i.e., if value is not zero)
        self.set_flag(FLAG_V, value == 0x8000); // set overflow flag if negating the most negative number (0x8000) causes overflow
    }

    fn alu_inc(&mut self, dest: usize) {
        let value = self.reg[dest] as u32;
        let result = value.wrapping_add(1);
        self.reg[dest] = result as u16; // store the lower 16 bits of the result in the destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
        //INC, DEC do not affect Carry flag   
        self.set_flag(FLAG_V, value == 0x7FFF); // set overflow flag if incrementing the most positive number (0x7FFF) causes overflow
    }

    fn alu_dec(&mut self, dest: usize) {
        let value = self.reg[dest] as u32;
        let result = value.wrapping_sub(1);
        self.reg[dest] = result as u16; // store the lower 16 bits of the result in the destination register
        self.update_flags_nz(self.reg[dest]); // update zero and negative flags based on the result
        //INC, DEC do not affect Carry flag   
        self.set_flag(FLAG_V, value == 0x8000); // set overflow flag if decrementing the most negative number (0x8000) causes overflow
    }

    fn fetch(&mut self) -> u32 {
        let pc = self.reg[REG_PC];
        let instruction = self.read32(pc); // fetch 32-bit instruction from memory at the address pointed to by PC
        self.reg[REG_PC] = pc.wrapping_add(4); // increment PC by 4 to point to the next instruction (since each instruction is 4 bytes)
        instruction // return the fetched instruction
    }

    fn decode(&self, instruction: u32) -> (u8, usize, usize, usize, u16) {
        let opcode = ((instruction >> 24) & 0xFF) as u8; // extract opcode (bits 24-31)
        let dest_reg = ((instruction >> 20) & 0xF) as usize; // extract destination register index (bits 20-23)
        let src1_reg = ((instruction >> 16) & 0xF) as usize; // extract source register 1 index (bits 16-19)
        let src2_reg = ((instruction >> 12) & 0xF) as usize; // extract source register 2 index (bits 12-15)
        let imm_val = (instruction & 0xFFFF) as u16; // extract immediate value (bits 0-15)
        (opcode, dest_reg, src1_reg, src2_reg, imm_val) // return the decoded components of the instruction
    }

    fn execute(&mut self, opcode: u8, dest_reg: usize, src1_reg: usize, src2_reg: usize, imm_val: u16) {
        match opcode {
            // Implement instruction execution logic based on opcode
            0x00 => { /* NOP - No operation */ }
            0x01 => self.reg[dest_reg] = self.reg[src1_reg], // MOV
            0x02 => self.reg[dest_reg] = self.read(self.reg[src1_reg]), // LD
            0x03 => self.write(self.reg[dest_reg], self.reg[src1_reg]), // ST
            0x04 => self.reg[dest_reg] = imm_val, // LDI
            0x05 => self.alu_add(dest_reg, src1_reg, src2_reg), // ADD
            0x06 => self.alu_sub(dest_reg, src1_reg, src2_reg), // SUB
            0x07 => self.reg[REG_PC] = imm_val, // JMP
            0x08 => if self.get_flag(FLAG_Z) { self.reg[REG_PC] = imm_val; } // JZ
            0x09 => if !self.get_flag(FLAG_Z) { self.reg[REG_PC] = imm_val; } // JNZ
            0x0A => self.push(self.reg[src1_reg]), // PUSH
            0x0B => self.reg[dest_reg] = self.pop(), // POP
            0x0C => {
                self.push(self.reg[REG_PC]); // push return address onto stack
                self.reg[REG_PC] = imm_val; // jump to subroutine
            }
            0x0D => self.reg[REG_PC] = self.pop(), // RET
            0x0E => {
                self.push(self.flags); // push FLAGS onto stack
                self.push(self.reg[REG_PC]); // push PC onto stack  
                self.set_flag(FLAG_I, false); // clear I flag to disable further interrupts
                let vector_address = 0xFF00 + ((imm_val & 0x7F) * 2); // calculate interrupt vector address
                self.reg[REG_PC] = self.read(vector_address); // set PC to the address of the interrupt handler
            }
            0x0F => {
                self.reg[REG_PC] = self.pop(); // pop PC from stack
                self.flags = self.pop(); // pop FLAGS from stack
            }
            0x10 => self.set_flag(FLAG_I, true), // EI - Enable interrupts
            0x11 => self.set_flag(FLAG_I, false), // DI - Disable interrupts
            0x12 => self.alu_and(dest_reg, src1_reg, src2_reg), // AND
            0x13 => self.alu_or(dest_reg, src1_reg, src2_reg), // OR
            0x14 => self.alu_xor(dest_reg, src1_reg, src2_reg), // XOR
            0x15 => self.alu_shl(dest_reg, src1_reg, imm_val), // SHL
            0x16 => self.alu_shr(dest_reg, src1_reg, imm_val), // SHR
            0x17 => self.alu_cmp(src1_reg, src2_reg), // CMP
            0x18 => self.alu_test(src1_reg, src2_reg), // TEST
            0x19 => self.alu_not(dest_reg, src1_reg), // NOT
            0x1A => self.alu_inc(dest_reg), // INC
            0x1B => self.alu_dec(dest_reg), // DEC
            0x1C => self.alu_neg(dest_reg, src1_reg), // NEG
            0x1D => {
                self.push(imm_val); // PUSHI - Push immediate value onto stack
            }
            0x1E => self.reg[REG_PC] = self.reg[REG_PC].wrapping_add(self.reg[src1_reg]), // JR - Jump relative using register value
            0x1F => if self.get_flag(FLAG_Z) { self.reg[REG_PC] = self.reg[REG_PC].wrapping_add(self.reg[src1_reg]); } // JZR - Jump relative if zero flag is set using register value
            0x20 => if !self.get_flag(FLAG_Z) { self.reg[REG_PC] = self.reg[REG_PC].wrapping_add(self.reg[src1_reg]); } // JNZR - Jump relative if zero flag is not set using register value
            0x21 => if self.get_flag(FLAG_C) { self.reg[REG_PC] = self.reg[REG_PC].wrapping_add(self.reg[src1_reg]); } // JC - Jump if carry flag is set using register value
            0x22 => if !self.get_flag(FLAG_C) { self.reg[REG_PC] = self.reg[REG_PC].wrapping_add(self.reg[src1_reg]); } // JNC - Jump if carry flag is not set using register value
            0x23 => self.reg[REG_PC] = self.reg[REG_PC].wrapping_add(imm_val), // JRI - Jump relative immediate
            0x24 => self.reg[dest_reg] = self.reg[src1_reg].wrapping_add(imm_val), // LEA - Load effective address
            0x25 => self.write(self.reg[dest_reg], imm_val), // STI - Store immediate value to memory address formed by dst_reg
            0x26 => self.reg[dest_reg] = self.read(self.reg[src1_reg]), // LDB - Load byte from memory address formed by src1_reg into dst_reg
            0x27 => self.write(self.reg[dest_reg], self.reg[src1_reg] & 0xFF), // STB - Store byte from src1_reg into memory address formed by dst_reg (only write the lower 8 bits)
            0x28 => {
                self.running = false; // WAIT - Put CPU in not running state until an interrupt occurs
            }
            0xFD => {
                // CPUID - Return CPU information in registers
                self.reg[1] = 0x0000; // Vendor ID (currently 0x0000 only)
                self.reg[2] = CPU_EXTENSION_LEVEL as u16; // Extension Level (e.g., 0 for EL0, 1 for EL1, etc.)
                // Additional feature flags can be set in other registers if needed
            }
            0xFE => {
                self.reset(); // RESET - Reset the CPU to initial state
            }
            0xFF => {
                self.running = false; // HALT - Stop execution
            }
            _ => {
                eprintln!("Unhandled opcode: 0x{:>02X}", opcode);
            }
        }
    }

    fn step(&mut self) {
        if !self.running {
            return; // if CPU is not running, skip execution
        }
        let instruction = self.fetch(); // fetch the next instruction
        let (opcode, dest_reg, src1_reg, src2_reg, imm_val) = self.decode(instruction); // decode the instruction
        self.execute(opcode, dest_reg, src1_reg, src2_reg, imm_val); // execute the instruction
        self.reg[0] = 0; // ensure R0 always reads as 0
    }

    fn run(&mut self) {
        while self.running {
            self.step(); // continuously execute instructions until CPU is halted
        }
    }
}

fn load_program(cpu: &mut CPU, program: &[u8], start_addr: u16) {
    for (i, byte) in program.iter().enumerate() {
        cpu.write8(start_addr + i as u16, *byte); // load the program bytes into memory starting at the specified address
    }
}

use std::env;
fn main () {
    let mut cpu = CPU::new();
    println!("Hello, SRC16 CPU Emulator in Rust!\n");
    let file_path = env::args().nth(1).unwrap_or_else(|| "../work/prog.a.bin".into());
    let program = std::fs::read(file_path).expect("Failed to read program file");
    load_program(&mut cpu, &program, 0); // Load the program into memory    
    cpu.run();
    println!("CPU halted. Final register state:");
    for i in 0..16 {
        print!("R{}: 0x{:04X} ", i, cpu.reg[i]);
        if (i + 1) % 4 == 0 {
            println!();
        }
    }
    println!("FLAGS: Z={} N={} C={} V={} I={}", cpu.get_flag(FLAG_Z) as u8, cpu.get_flag(FLAG_N) as u8, cpu.get_flag(FLAG_C) as u8, cpu.get_flag(FLAG_V) as u8, cpu.get_flag(FLAG_I) as u8);
    println!("Memory dump (0x0000-0x00FF):");
    for addr in 0x0000..=0x00FF {
        if addr % 16 == 0 {
            print!("\n0x{:04X}: ", addr);
        }
        print!("{:02X} ", cpu.read8(addr));
        if addr % 16 == 15 {
            print!("| ");
            for i in 0..16 {
                let byte = cpu.read8(addr - 15 + i);
                let ch = if byte.is_ascii_graphic() || byte == b' ' { byte as char } else { '.' };
                print!("{}", ch);
            }
        }
    }
    println!();
}