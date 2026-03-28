--[[
# SRC16 (Scalable RISC 16-bit CPU)

Educational fantasy CPU emulator, minimalistic and designed for learning purposes.
16-bit, big-endian, 16-bit address space, 16 general-purpose registers (R0-R15) and flag register, and a simple instruction set.
]]

local CPU = {}
local bit32 = {}
bit32.lshift = function(value, shift)
    return value * (2 ^ shift)
end
bit32.rshift = function(value, shift)
    return math.floor(value / (2 ^ shift))
end
bit32.band = function(a, b)
    local result = 0
    local bit = 1
    while a > 0 and b > 0 do
        if (a % 2 == 1) and (b % 2 == 1) then
            result = result + bit
        end
        a = math.floor(a / 2)
        b = math.floor(b / 2)
        bit = bit * 2
    end
    return result
end
bit32.bor = function(a, b)
    local result = 0
    local bit = 1
    while a > 0 or b > 0 do
        if (a % 2 == 1) or (b % 2 == 1) then
            result = result + bit
        end
        a = math.floor(a / 2)
        b = math.floor(b / 2)
        bit = bit * 2
    end
    return result
end
bit32.bxor = function(a, b)
    local result = 0
    local bit = 1
    while a > 0 or b > 0 do
        if (a % 2) ~= (b % 2) then
            result = result + bit
        end
        a = math.floor(a / 2)
        b = math.floor(b / 2)
        bit = bit * 2
    end
    return result
end


CPU.__index = CPU

-- Constants
CPU.FLAG_Z = bit32.lshift(1, 0)  -- Zero flag
CPU.FLAG_N = bit32.lshift(1, 1)  -- Negative flag
CPU.FLAG_C = bit32.lshift(1, 2)  -- Carry flag
CPU.FLAG_V = bit32.lshift(1, 3)  -- Overflow flag
CPU.FLAG_I = bit32.lshift(1, 4)  -- Interrupt enable flag

CPU.STACK_START = 0xFD00  -- Start of stack area in memory
CPU.STACK_SIZE = 0x100    -- 256 bytes
CPU.STACK_END = CPU.STACK_START + CPU.STACK_SIZE  -- Empty stack pointer
CPU.STACK_ENTRIES = bit32.rshift(CPU.STACK_SIZE, 1)  -- 128 entries of 16-bit data

CPU.CPU_EXTENSION_LEVEL = 1  -- Current CPU Extension Level

-- Exception classes
local CPUError = {}
CPUError.__index = CPUError

function CPUError:new(message, pc, instr, cpu)
    local self = setmetatable({}, CPUError)
    self.message = message
    self.pc = pc
    self.instr = instr
    self.cpu = cpu
    return self
end

function CPUError:__tostring()
    local pc_before = bit32.band(self.pc - 4, 0xFFFF)
    local txt = ""
    
    if self.instr ~= nil then
        txt = string.format("CPU Error at PC=%04X (Instr=%08X): %s\n", 
                           pc_before, self.instr, self.message)
    else
        txt = string.format("CPU Error at PC=%04X: %s\n", pc_before, self.message)
    end
    
    txt = txt .. "Final register state:\n"
    for i = 0, 15 do
        local reg_val = self.cpu.reg[i+1]
        if i == 14 then
            txt = txt .. string.format("R%d (SP): %04X\n", i, reg_val)
        elseif i == 15 then
            txt = txt .. string.format("R%d (PC): %04X\n", i, reg_val)
        elseif i == 0 then
            txt = txt .. string.format("R%d (Zero): %04X\n", i, reg_val)
        else
            txt = txt .. string.format("R%2d: %04X\n", i, reg_val)
        end
    end
    
    txt = txt .. string.format("FLAG: %s\n", string.format("%016b", self.cpu.flag))
    
    local dump_start = bit32.band(bit32.rshift(self.pc, 8) * 256, 0xFFFF)
    txt = txt .. string.format("Memory dump (0x%04X):\n", dump_start)
    for i = dump_start, math.min(dump_start + 256 - 1, 0xFFFF), 16 do
        local chunk_str = ""
        local ascii_str = ""
        for j = 0, 15 do
            if i + j <= 0xFFFF then
                local byte_val = self.cpu.mem[i + j + 1] or 0
                chunk_str = chunk_str .. string.format("%02X ", byte_val)
                ascii_str = ascii_str .. (byte_val >= 32 and byte_val <= 126 and string.char(byte_val) or '.')
            end
        end
        txt = txt .. string.format("%04X: %s %s\n", i, chunk_str, ascii_str)
    end
    
    return txt
end

local InvalidOpcodeError = setmetatable({}, {__index = CPUError})
InvalidOpcodeError.__index = InvalidOpcodeError

function InvalidOpcodeError:new(opcode, pc, instr, cpu)
    local self = setmetatable({}, InvalidOpcodeError)
    self.message = string.format("Invalid opcode: %02X", opcode)
    self.pc = pc
    self.instr = instr
    self.cpu = cpu
    self.opcode = opcode
    return self
end

local StackOverflowError = setmetatable({}, {__index = CPUError})
StackOverflowError.__index = StackOverflowError

function StackOverflowError:new(pc, cpu)
    local self = setmetatable({}, StackOverflowError)
    self.message = "Stack overflow"
    self.pc = pc
    self.instr = nil
    self.cpu = cpu
    return self
end

local StackUnderflowError = setmetatable({}, {__index = CPUError})
StackUnderflowError.__index = StackUnderflowError

function StackUnderflowError:new(pc, cpu)
    local self = setmetatable({}, StackUnderflowError)
    self.message = "Stack underflow"
    self.pc = pc
    self.instr = nil
    self.cpu = cpu
    return self
end

local MemoryAccessError = setmetatable({}, {__index = CPUError})
MemoryAccessError.__index = MemoryAccessError

function MemoryAccessError:new(address, pc, cpu)
    local self = setmetatable({}, MemoryAccessError)
    self.message = string.format("Invalid memory access at address: %04X", address)
    self.pc = pc
    self.instr = nil
    self.cpu = cpu
    self.address = address
    return self
end

-- CPU Constructor
function CPU:new()
    local self = setmetatable({}, CPU)
    self.mem = {}
    -- Initialize memory to 0x10000 (64KB)
    for i = 0, 0xFFFF do
        self.mem[i + 1] = 0
    end
    self:reset()
    return self
end

function CPU:reset()
    -- Reset CPU state to initial conditions
    self.reg = {}
    for i = 0, 15 do
        self.reg[i + 1] = 0
    end
    self.flag = 0
    self.running = true
    self.cycle = 0
    self:set_pc(0x0000)
    self:set_sp(self.STACK_END)
end

-- PC and SP properties
function CPU:get_pc()
    return self.reg[16]  -- R15 is PC
end

function CPU:set_pc(val)
    self.reg[16] = bit32.band(val, 0xFFFF)
end

function CPU:get_sp()
    return self.reg[15]  -- R14 is SP
end

function CPU:set_sp(val)
    self.reg[15] = bit32.band(val, 0xFFFF)
end

-- Memory operations
function CPU:mem8_read(addr)
    addr = bit32.band(addr, 0xFFFF)
    return self.mem[addr + 1] or 0
end

function CPU:mem8_write(addr, val)
    addr = bit32.band(addr, 0xFFFF)
    self.mem[addr + 1] = bit32.band(val, 0xFF)
end

function CPU:io8_read(addr)
    if addr == 0xFE00 then  -- UART I/O register
        local ch = io.read(1)
        return ch and string.byte(ch) or 0
    elseif addr == 0xFE01 then  -- UART status register
        -- Bit 0: input ready, Bit 1: output ready
        -- For now, simplified: always output ready
        return 2  -- output ready (bit 1)
    end
    return 0
end

function CPU:io8_write(addr, val)
    if addr == 0xFE00 then  -- UART I/O register
        io.write(string.char(bit32.band(val, 0xFF)))
        io.flush()
    end
end

function CPU:read8(addr)
    addr = bit32.band(addr, 0xFFFF)
    if addr >= 0xFE00 and addr <= 0xFEFF then
        return self:io8_read(addr)
    else
        return self:mem8_read(addr)
    end
end

function CPU:read16(addr)
    local hi = self:read8(addr)
    local lo = self:read8(bit32.band(addr + 1, 0xFFFF))
    return bit32.bor(bit32.lshift(hi, 8), lo)
end

function CPU:read32(addr)
    local hi = self:read16(addr)
    local lo = self:read16(bit32.band(addr + 2, 0xFFFF))
    return bit32.bor(bit32.lshift(hi, 16), lo)
end

function CPU:write8(addr, val)
    addr = bit32.band(addr, 0xFFFF)
    if addr >= 0xFE00 and addr <= 0xFEFF then
        self:io8_write(addr, val)
    else
        self:mem8_write(addr, val)
    end
end

function CPU:write16(addr, val)
    val = bit32.band(val, 0xFFFF)
    self:write8(addr, bit32.rshift(val, 8))
    self:write8(bit32.band(addr + 1, 0xFFFF), val)
end

function CPU:write32(addr, val)
    val = bit32.band(val, 0xFFFFFFFF)
    self:write16(addr, bit32.rshift(val, 16))
    self:write16(bit32.band(addr + 2, 0xFFFF), val)
end

function CPU:read(addr)
    -- Handle both 8-bit I/O and 16-bit memory access
    if addr >= 0xFE00 and addr <= 0xFEFF then
        return self:read8(addr)
    else
        return self:read16(addr)
    end
end

function CPU:write(addr, val)
    -- Handle both 8-bit I/O and 16-bit memory access
    if addr >= 0xFE00 and addr <= 0xFEFF then
        self:write8(addr, val)
    else
        self:write16(addr, val)
    end
end

function CPU:sign16(val)
    val = bit32.band(val, 0xFFFF)
    if val >= 0x8000 then
        return val - 0x10000
    else
        return val
    end
end

-- Stack operations
function CPU:push(val)
    if self:get_sp() < self.STACK_START + 2 then
        error(StackOverflowError:new(self:get_pc(), self))
    end
    self:set_sp(bit32.band(self:get_sp() - 2, 0xFFFF))
    self:write16(self:get_sp(), val)
end

function CPU:pop()
    if self:get_sp() >= self.STACK_END then
        error(StackUnderflowError:new(self:get_pc(), self))
    end
    local value = self:read16(self:get_sp())
    self:set_sp(bit32.band(self:get_sp() + 2, 0xFFFF))
    return value
end

-- Flag operations
function CPU:set_flag(flag, cond)
    if cond then
        self.flag = bit32.bor(self.flag, flag)
    else
        self.flag = bit32.band(self.flag, bit32.bnot(flag))
    end
end

function CPU:get_flag(flag)
    return bit32.band(self.flag, flag) ~= 0
end

function CPU:update_flags_nz(val)
    val = bit32.band(val, 0xFFFF)
    self:set_flag(self.FLAG_Z, val == 0)
    self:set_flag(self.FLAG_N, bit32.band(val, 0x8000) ~= 0)
end

-- ALU operations
function CPU:alu_add(a, b)
    a = bit32.band(a, 0xFFFF)
    b = bit32.band(b, 0xFFFF)
    local result_full = a + b
    local result = bit32.band(result_full, 0xFFFF)
    
    self:update_flags_nz(result)
    self:set_flag(self.FLAG_C, result_full >= 0x10000)
    
    -- Overflow: (a ^ result) & (b ^ result) & 0x8000
    local overflow = bit32.band(bit32.bxor(a, result), 
                               bit32.bxor(b, result), 0x8000)
    self:set_flag(self.FLAG_V, overflow ~= 0)
    
    return result
end

function CPU:alu_sub(a, b)
    a = bit32.band(a, 0xFFFF)
    b = bit32.band(b, 0xFFFF)
    local result_full = a - b
    local result = bit32.band(result_full, 0xFFFF)
    
    self:update_flags_nz(result)
    self:set_flag(self.FLAG_C, a < b)
    
    -- Overflow: (a ^ b) & (a ^ result) & 0x8000
    local overflow = bit32.band(bit32.bxor(a, b), 
                               bit32.bxor(a, result), 0x8000)
    self:set_flag(self.FLAG_V, overflow ~= 0)
    
    return result
end

function CPU:alu_and(a, b)
    local result = bit32.band(bit32.band(a, b), 0xFFFF)
    self:update_flags_nz(result)
    return result
end

function CPU:alu_or(a, b)
    local result = bit32.band(bit32.bor(a, b), 0xFFFF)
    self:update_flags_nz(result)
    return result
end

function CPU:alu_xor(a, b)
    local result = bit32.band(bit32.bxor(a, b), 0xFFFF)
    self:update_flags_nz(result)
    return result
end

function CPU:alu_cmp(a, b)
    self:alu_sub(a, b)
end

function CPU:alu_test(a, b)
    self:alu_and(a, b)
end

function CPU:alu_shl(a, shift)
    a = bit32.band(a, 0xFFFF)
    local shift_amount = bit32.band(shift, 0x0F)
    
    if shift_amount == 0 then
        return bit32.band(a, 0xFFFF)
    end
    
    local result = bit32.band(bit32.lshift(a, shift_amount), 0xFFFF)
    self:update_flags_nz(result)
    
    local carry = bit32.band(bit32.rshift(a, 16 - shift_amount), 1)
    self:set_flag(self.FLAG_C, carry ~= 0)
    
    return result
end

function CPU:alu_shr(a, shift)
    a = bit32.band(a, 0xFFFF)
    local shift_amount = bit32.band(shift, 0x0F)
    
    if shift_amount == 0 then
        return bit32.band(a, 0xFFFF)
    end
    
    local result = bit32.band(bit32.rshift(a, shift_amount), 0xFFFF)
    self:update_flags_nz(result)
    
    local carry = bit32.band(bit32.rshift(a, shift_amount - 1), 1)
    self:set_flag(self.FLAG_C, carry ~= 0)
    
    return result
end

function CPU:alu_not(a)
    local result = bit32.band(bit32.bnot(a), 0xFFFF)
    self:update_flags_nz(result)
    return result
end

function CPU:alu_neg(a)
    a = bit32.band(a, 0xFFFF)
    local result = bit32.band((-a), 0xFFFF)
    
    self:update_flags_nz(result)
    self:set_flag(self.FLAG_C, a ~= 0)
    self:set_flag(self.FLAG_V, a == 0x8000)
    
    return result
end

function CPU:alu_inc(a)
    a = bit32.band(a, 0xFFFF)
    local result_full = a + 1
    local result = bit32.band(result_full, 0xFFFF)
    
    self:update_flags_nz(result)
    self:set_flag(self.FLAG_V, a == 0x7FFF)
    
    return result
end

function CPU:alu_dec(a)
    a = bit32.band(a, 0xFFFF)
    local result_full = a - 1
    local result = bit32.band(result_full, 0xFFFF)
    
    self:update_flags_nz(result)
    self:set_flag(self.FLAG_V, a == 0x8000)
    
    return result
end

-- Instruction fetch/decode/execute
function CPU:fetch()
    local pc = self:get_pc()
    local instr = self:read32(pc)
    self:set_pc(bit32.band(self:get_pc() + 4, 0xFFFF))
    return instr
end

function CPU:decode(instr)
    local opcode = bit32.band(bit32.rshift(instr, 24), 0xFF)
    local dest_reg = bit32.band(bit32.rshift(instr, 20), 0x0F)
    local src1_reg = bit32.band(bit32.rshift(instr, 16), 0x0F)
    local src2_reg = bit32.band(bit32.rshift(instr, 12), 0x0F)
    local imm_val = bit32.band(instr, 0xFFFF)
    
    return opcode, dest_reg, src1_reg, src2_reg, imm_val
end

function CPU:execute(opcode, dst_reg, src1_reg, src2_reg, imm_val, instr)
    local result
    
    if opcode == 0x00 then  -- NOP
        -- No operation
        
    elseif opcode == 0x01 then  -- MOV dst_reg, src1_reg
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = bit32.band(self.reg[src1_reg + 1], 0xFFFF)
        end
        
    elseif opcode == 0x02 then  -- LD dst_reg, [src1_reg]
        if dst_reg ~= 0 then
            local addr = bit32.band(self.reg[src1_reg + 1], 0xFFFF)
            self.reg[dst_reg + 1] = bit32.band(self:read(addr), 0xFFFF)
        end
        
    elseif opcode == 0x03 then  -- ST [dst_reg], src1_reg
        local addr = bit32.band(self.reg[dst_reg + 1], 0xFFFF)
        local val = bit32.band(self.reg[src1_reg + 1], 0xFFFF)
        self:write(addr, val)
        
    elseif opcode == 0x04 then  -- LDI dst_reg, imm_val
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = bit32.band(imm_val, 0xFFFF)
        end
        
    elseif opcode == 0x05 then  -- ADD dst_reg, src1_reg, src2_reg
        result = self:alu_add(self.reg[src1_reg + 1], self.reg[src2_reg + 1])
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x06 then  -- SUB dst_reg, src1_reg, src2_reg
        result = self:alu_sub(self.reg[src1_reg + 1], self.reg[src2_reg + 1])
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x07 then  -- JMP imm_val
        self:set_pc(bit32.band(imm_val, 0xFFFF))
        
    elseif opcode == 0x08 then  -- JZ imm_val
        if self:get_flag(self.FLAG_Z) then
            self:set_pc(bit32.band(imm_val, 0xFFFF))
        end
        
    elseif opcode == 0x09 then  -- JNZ imm_val
        if not self:get_flag(self.FLAG_Z) then
            self:set_pc(bit32.band(imm_val, 0xFFFF))
        end
        
    elseif opcode == 0x0A then  -- PUSH src_reg
        self:push(self.reg[src1_reg + 1])
        
    elseif opcode == 0x0B then  -- POP dst_reg
        local val = self:pop()
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = val
        end
        
    elseif opcode == 0x0C then  -- CALL imm_val
        self:push(self:get_pc())
        self:set_pc(bit32.band(imm_val, 0xFFFF))
        
    elseif opcode == 0x0D then  -- RET
        self:set_pc(self:pop())
        
    elseif opcode == 0x0E then  -- INT imm_val
        self:push(self.flag)
        self:push(self:get_pc())
        self:set_flag(self.FLAG_I, false)
        local vector_address = 0xFF00 + bit32.band(imm_val, 0x7F) * 2
        self:set_pc(self:read16(vector_address))
        
    elseif opcode == 0x0F then  -- IRET
        self:set_pc(self:pop())
        self.flag = self:pop()
        
    elseif opcode == 0x10 then  -- EI
        self:set_flag(self.FLAG_I, true)
        
    elseif opcode == 0x11 then  -- DI
        self:set_flag(self.FLAG_I, false)
        
    elseif opcode == 0xFD then  -- CPUID
        self.reg[2] = 0x0000  -- Vendor ID (R1)
        self.reg[3] = self.CPU_EXTENSION_LEVEL  -- Extension Level (R2)
        
    elseif opcode == 0xFE then  -- RESET
        self:reset()
        
    elseif opcode == 0xFF then  -- HALT
        self.running = false
        
    -- EL1 Extended Instructions
    elseif opcode == 0x12 then  -- AND dst_reg, src1_reg, src2_reg
        result = self:alu_and(self.reg[src1_reg + 1], self.reg[src2_reg + 1])
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x13 then  -- OR dst_reg, src1_reg, src2_reg
        result = self:alu_or(self.reg[src1_reg + 1], self.reg[src2_reg + 1])
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x14 then  -- XOR dst_reg, src1_reg, src2_reg
        result = self:alu_xor(self.reg[src1_reg + 1], self.reg[src2_reg + 1])
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x15 then  -- SHL dst_reg, src1_reg, imm_val
        result = self:alu_shl(self.reg[src1_reg + 1], imm_val)
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x16 then  -- SHR dst_reg, src1_reg, imm_val
        result = self:alu_shr(self.reg[src1_reg + 1], imm_val)
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x17 then  -- CMP src1_reg, src2_reg
        self:alu_cmp(self.reg[src1_reg + 1], self.reg[src2_reg + 1])
        
    elseif opcode == 0x18 then  -- TEST src1_reg, src2_reg
        self:alu_test(self.reg[src1_reg + 1], self.reg[src2_reg + 1])
        
    elseif opcode == 0x19 then  -- NOT dst_reg, src1_reg
        result = self:alu_not(self.reg[src1_reg + 1])
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x1A then  -- INC dst_reg
        result = self:alu_inc(self.reg[dst_reg + 1])
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x1B then  -- DEC dst_reg
        result = self:alu_dec(self.reg[dst_reg + 1])
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x1C then  -- NEG dst_reg, src1_reg
        result = self:alu_neg(self.reg[src1_reg + 1])
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = result
        end
        
    elseif opcode == 0x1D then  -- PUSHI imm_val
        self:push(imm_val)
        
    elseif opcode == 0x1E then  -- JR src_reg
        local offset = self:sign16(self.reg[src1_reg + 1])
        self:set_pc(bit32.band(self:get_pc() + offset, 0xFFFF))
        
    elseif opcode == 0x1F then  -- JZR src_reg
        if self:get_flag(self.FLAG_Z) then
            local offset = self:sign16(self.reg[src1_reg + 1])
            self:set_pc(bit32.band(self:get_pc() + offset, 0xFFFF))
        end
        
    elseif opcode == 0x20 then  -- JNZR src_reg
        if not self:get_flag(self.FLAG_Z) then
            local offset = self:sign16(self.reg[src1_reg + 1])
            self:set_pc(bit32.band(self:get_pc() + offset, 0xFFFF))
        end
        
    elseif opcode == 0x21 then  -- JC src_reg
        if self:get_flag(self.FLAG_C) then
            local offset = self:sign16(self.reg[src1_reg + 1])
            self:set_pc(bit32.band(self:get_pc() + offset, 0xFFFF))
        end
        
    elseif opcode == 0x22 then  -- JNC src_reg
        if not self:get_flag(self.FLAG_C) then
            local offset = self:sign16(self.reg[src1_reg + 1])
            self:set_pc(bit32.band(self:get_pc() + offset, 0xFFFF))
        end
        
    elseif opcode == 0x23 then  -- JRI imm_val
        local offset = self:sign16(imm_val)
        self:set_pc(bit32.band(self:get_pc() + offset, 0xFFFF))
        
    elseif opcode == 0x24 then  -- LEA dst_reg, src1_reg, imm_val
        local addr = bit32.band(self.reg[src1_reg + 1] + imm_val, 0xFFFF)
        if dst_reg ~= 0 then
            self.reg[dst_reg + 1] = addr
        end
        
    elseif opcode == 0x25 then  -- STI dst_reg, imm_val
        local addr = bit32.band(self.reg[dst_reg + 1], 0xFFFF)
        local val = bit32.band(imm_val, 0xFFFF)
        self:write16(addr, val)
        
    elseif opcode == 0x26 then  -- LDB dst_reg, [src1_reg]
        if dst_reg ~= 0 then
            local addr = bit32.band(self.reg[src1_reg + 1], 0xFFFF)
            self.reg[dst_reg + 1] = bit32.band(self:read8(addr), 0xFF)
        end
        
    elseif opcode == 0x27 then  -- STB [dst_reg], src1_reg
        local addr = bit32.band(self.reg[dst_reg + 1], 0xFFFF)
        local val = bit32.band(self.reg[src1_reg + 1], 0xFF)
        self:write8(addr, val)
        
    else  -- Invalid opcode
        error(InvalidOpcodeError:new(opcode, self:get_pc(), instr, self))
    end
end

function CPU:step()
    local instr = self:fetch()
    local opcode, dest_reg, src1_reg, src2_reg, imm_val = self:decode(instr)
    self:execute(opcode, dest_reg, src1_reg, src2_reg, imm_val, instr)
    self.reg[1] = 0  -- R0 is always zero
    self.cycle = self.cycle + 1
end

function CPU:run()
    while self.running do
        self:step()
    end
end

local cpu = CPU:new()

-- LDI R1, 42
cpu:write32(0x0000, 0x0410002A)
-- HALT
cpu:write32(0x0004, 0xFF000000)

cpu:run()
print(string.format("R1: %04X", cpu.reg[2]))  -- Should print R1: 002A

