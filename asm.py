import re
import struct
import sys

REGS = {f"R{i}": i for i in range(16)}
REGS["SP"] = 14
REGS["PC"] = 15

OPCODES = {
    "NOP":0x00,
    "MOV":0x01,"LD":0x02,"ST":0x03,"LDI":0x04,
    "ADD":0x05,"SUB":0x06,
    "JMP":0x07,"JZ":0x08,"JNZ":0x09,
    "PUSH":0x0A,"POP":0x0B,
    "CALL":0x0C,"RET":0x0D,
    "INT":0x0E,"IRET":0x0F,"EI":0x10,"DI":0x11,
    "AND":0x12,"OR":0x13,"XOR":0x14,
    "SHL":0x15,"SHR":0x16,
    "CMP":0x17,"TEST":0x18,
    "NOT":0x19,"INC":0x1A,"DEC":0x1B,"NEG":0x1C,
    "WAIT":0x1D,"PUSHI":0x1E,
    "JR":0x1F,"JZR":0x20,"JNZR":0x21,"JC":0x22,"JNC":0x23,"JRI":0x24,
    "LEA":0x25,
    "CPUID":0xFD,"RESET":0xFE,"HALT":0xFF
}

def parse_number(x):
    x = x.strip()
    if x.startswith("0x"):
        return int(x,16)
    if x.startswith("0b"):
        return int(x,2)
    return int(x)

def tokenize(line):
    line=line.split(";")[0].strip()
    if not line:
        return []
    line=line.replace(","," ")
    return line.split()

class Assembler:

    def __init__(self):
        self.symbols={}
        self.output=bytearray()
        self.pc=0
        self.lines=[]

    def load(self, text):
        self.lines=text.splitlines()

    def pass1(self):
        self.pc=0
        for line in self.lines:

            line=line.split(";")[0].strip()
            if not line:
                continue

            if line.endswith(":"):
                label=line[:-1]
                self.symbols[label]=self.pc
                continue

            tokens=tokenize(line)
            if not tokens:
                continue

            if tokens[0]==".org":
                self.pc=parse_number(tokens[1])
                continue

            if tokens[0]==".word":
                self.pc+=2
                continue

            self.pc+=4

    def reg(self,r):
        r=r.upper()
        if r not in REGS:
            raise Exception("invalid register "+r)
        return REGS[r]

    def imm(self,x):
        if x in self.symbols:
            return self.symbols[x]
        return parse_number(x)

    def encode_R(self,op,d,s1=0,s2=0):
        return (op<<24)|(d<<20)|(s1<<16)|(s2<<12)

    def encode_I(self,op,d,s1,imm):
        return (op<<24)|(d<<20)|(s1<<16)|(imm & 0xFFFF)

    def emit32(self,val):
        self.output += struct.pack(">I",val)

    def emit16(self,val):
        self.output += struct.pack(">H",val)

    def pass2(self):
        self.pc=0

        for line in self.lines:

            raw=line
            line=line.split(";")[0].strip()
            if not line:
                continue

            if line.endswith(":"):
                continue

            tokens=tokenize(line)
            if not tokens:
                continue

            op=tokens[0].upper()

            if op==".ORG":
                self.pc=parse_number(tokens[1])
                continue

            if op==".WORD":
                self.emit16(self.imm(tokens[1]))
                self.pc+=2
                continue

            opcode=OPCODES[op]

            # simple
            if op in ["NOP","RET","IRET","EI","DI","WAIT","CPUID","RESET","HALT"]:
                self.emit32(self.encode_R(opcode,0,0,0))

            elif op=="MOV":
                d=self.reg(tokens[1])
                s=self.reg(tokens[2])
                self.emit32(self.encode_R(opcode,d,s,0))

            elif op=="LD":
                d=self.reg(tokens[1])
                s=self.reg(tokens[2].strip("[]"))
                self.emit32(self.encode_R(opcode,d,s,0))

            elif op=="ST":
                d=self.reg(tokens[1].strip("[]"))
                s=self.reg(tokens[2])
                self.emit32(self.encode_R(opcode,d,s,0))

            elif op in ["ADD","SUB","AND","OR","XOR"]:
                d=self.reg(tokens[1])
                s1=self.reg(tokens[2])
                s2=self.reg(tokens[3])
                self.emit32(self.encode_R(opcode,d,s1,s2))

            elif op in ["CMP","TEST"]:
                s1=self.reg(tokens[1])
                s2=self.reg(tokens[2])
                self.emit32(self.encode_R(opcode,0,s1,s2))

            elif op in ["NOT","NEG"]:
                d=self.reg(tokens[1])
                s=self.reg(tokens[2])
                self.emit32(self.encode_R(opcode,d,s,0))

            elif op in ["INC","DEC"]:
                d=self.reg(tokens[1])
                self.emit32(self.encode_R(opcode,d,0,0))

            elif op in ["PUSH"]:
                s=self.reg(tokens[1])
                self.emit32(self.encode_R(opcode,0,s,0))

            elif op in ["POP"]:
                d=self.reg(tokens[1])
                self.emit32(self.encode_R(opcode,d,0,0))

            elif op in ["JR","JZR","JNZR","JC","JNC"]:
                s=self.reg(tokens[1])
                self.emit32(self.encode_R(opcode,0,s,0))

            elif op in ["JMP","JZ","JNZ","CALL","INT"]:
                imm=self.imm(tokens[1])
                self.emit32(self.encode_I(opcode,0,0,imm))

            elif op in ["LDI","PUSHI","JRI"]:
                d=0
                s1=0
                if op=="LDI":
                    d=self.reg(tokens[1])
                    imm=self.imm(tokens[2])
                    self.emit32(self.encode_I(opcode,d,0,imm))
                elif op=="PUSHI":
                    imm=self.imm(tokens[1])
                    self.emit32(self.encode_I(opcode,0,0,imm))
                elif op=="JRI":
                    imm=self.imm(tokens[1])
                    self.emit32(self.encode_I(opcode,0,0,imm))

            elif op in ["SHL","SHR"]:
                d=self.reg(tokens[1])
                s=self.reg(tokens[2])
                imm=self.imm(tokens[3])
                self.emit32(self.encode_I(opcode,d,s,imm))

            elif op=="LEA":
                d=self.reg(tokens[1])
                s=self.reg(tokens[2])
                imm=self.imm(tokens[3])
                self.emit32(self.encode_I(opcode,d,s,imm))

            else:
                raise Exception("unknown instruction "+raw)

            self.pc+=4

    def assemble(self,text):
        self.load(text)
        self.pass1()
        self.pass2()
        return self.output
    
if __name__=="__main__":
    asm=Assembler()
    with open(sys.argv[1], "r") as f:
        code=f.read()
    binary=asm.assemble(code)
    with open(sys.argv[1]+".bin", "wb") as f:
        f.write(binary)
    print(f"Assembled code written to {sys.argv[1]}.bin")