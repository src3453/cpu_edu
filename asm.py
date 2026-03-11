import re
import struct
import sys

REGS = {f"R{i}": i for i in range(16)} | {"SP": 14, "PC": 15}

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
    "PUSHI":0x1D,
    "JR":0x1E,"JZR":0x1F,"JNZR":0x20,"JC":0x21,"JNC":0x22,"JRI":0x23,
    "LEA":0x24,"STI":0x25,
    "LDB":0x26,"STB":0x27,
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
    line = line.split(";")[0].strip()
    if not line:
        return []
    return re.findall(r'\[.*?\]|".*?"|[^,\s]+', line)


class Assembler:

    def __init__(self):
        self.symbols={}
        self.output=bytearray()
        self.pc=0
        self.lines=[]

    def load(self, text):
        self.lines=text.splitlines()

    def set_pc(self,newpc):
        if newpc < len(self.output):
            raise Exception("ORG overlaps existing code")
        while len(self.output) < newpc:
            self.output.append(0)
        self.pc=newpc

    def estimate_db_size(self,items):
        size=0
        for it in items:
            if it.startswith('"') and it.endswith('"'):
                size+=len(it.strip('"').encode())
            else:
                size+=1
        return size

    def pass1(self):
        self.pc=0
        for lineno,line in enumerate(self.lines,1):

            line=line.split(";")[0].strip()
            if not line:
                continue

            if line.endswith(":"):
                label=line[:-1]
                if label in self.symbols:
                    raise Exception(f"line {lineno}: duplicate label {label}")
                self.symbols[label]=self.pc
                continue

            tokens=tokenize(line)
            if not tokens:
                continue

            op=tokens[0].upper()

            if op==".ORG":
                self.pc=parse_number(tokens[1])
                continue

            if op==".WORD":
                self.pc+=2
                continue

            if op==".BYTE":
                self.pc+=1
                continue

            if op==".DB":
                self.pc+=self.estimate_db_size(tokens[1:])
                continue

            if op==".STRING":
                s=line.split(".STRING",1)[1].strip().strip('"')
                self.pc+=len(s.encode())
                continue

            self.pc+=4

    def reg(self,r,lineno):
        r=r.upper()
        if r not in REGS:
            raise Exception(f"line {lineno}: invalid register {r}")
        return REGS[r]

    def imm(self,x,lineno):
        if x in self.symbols:
            return self.symbols[x]
        try:
            return parse_number(x)
        except:
            raise Exception(f"line {lineno}: undefined symbol {x}")

    def encode_R(self,op,d,s1=0,s2=0):
        return (op<<24)|(d<<20)|(s1<<16)|(s2<<12)

    def encode_I(self,op,d,s1,imm):
        if not -32768 <= imm <= 65535:
            raise Exception(f"immediate out of range: {imm}")
        return (op<<24)|(d<<20)|(s1<<16)|(imm & 0xFFFF)

    def emit32(self,val):
        self.output += struct.pack(">I",val)
        self.pc+=4

    def emit16(self,val):
        self.output += struct.pack(">H",val)
        self.pc+=2

    def emit8(self,val):
        self.output.append(val & 0xFF)
        self.pc+=1

    def pass2(self):
        self.pc=0

        for lineno,line in enumerate(self.lines,1):

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
                self.set_pc(parse_number(tokens[1]))
                continue

            if op==".WORD":
                self.emit16(self.imm(tokens[1],lineno))
                continue

            if op==".BYTE":
                self.emit8(self.imm(tokens[1],lineno))
                continue

            if op==".DB":
                for item in tokens[1:]:
                    if item.startswith('"') and item.endswith('"'):
                        for c in item.strip('"').encode():
                            self.emit8(c)
                    else:
                        self.emit8(self.imm(item,lineno))
                continue

            if op==".STRING":
                s=line.split(".STRING",1)[1].strip().strip('"')
                for c in s.encode():
                    self.emit8(c)
                continue

            if op not in OPCODES:
                raise Exception(f"line {lineno}: unknown instruction {op}")

            opcode=OPCODES[op]

            if op in ["NOP","RET","IRET","EI","DI","CPUID","RESET","HALT"]:
                self.emit32(self.encode_R(opcode,0,0,0))

            elif op=="MOV":
                d=self.reg(tokens[1],lineno)
                s=self.reg(tokens[2],lineno)
                self.emit32(self.encode_R(opcode,d,s,0))

            elif op in ["LD","LDB"]:
                d=self.reg(tokens[1],lineno)
                s=self.reg(tokens[2].strip("[]"),lineno)
                self.emit32(self.encode_R(opcode,d,s,0))

            elif op in ["ST","STB"]:
                d=self.reg(tokens[1].strip("[]"),lineno)
                s=self.reg(tokens[2],lineno)
                self.emit32(self.encode_R(opcode,d,s,0))

            elif op in ["ADD","SUB","AND","OR","XOR"]:
                d=self.reg(tokens[1],lineno)
                s1=self.reg(tokens[2],lineno)
                s2=self.reg(tokens[3],lineno)
                self.emit32(self.encode_R(opcode,d,s1,s2))

            elif op in ["CMP","TEST"]:
                s1=self.reg(tokens[1],lineno)
                s2=self.reg(tokens[2],lineno)
                self.emit32(self.encode_R(opcode,0,s1,s2))

            elif op in ["NOT","NEG"]:
                d=self.reg(tokens[1],lineno)
                s=self.reg(tokens[2],lineno)
                self.emit32(self.encode_R(opcode,d,s,0))

            elif op in ["INC","DEC"]:
                d=self.reg(tokens[1],lineno)
                self.emit32(self.encode_R(opcode,d,0,0))

            elif op=="PUSH":
                s=self.reg(tokens[1],lineno)
                self.emit32(self.encode_R(opcode,0,s,0))

            elif op=="POP":
                d=self.reg(tokens[1],lineno)
                self.emit32(self.encode_R(opcode,d,0,0))

            elif op in ["JR","JZR","JNZR","JC","JNC"]:
                s=self.reg(tokens[1],lineno)
                self.emit32(self.encode_R(opcode,0,s,0))

            elif op in ["JMP","JZ","JNZ","CALL","INT"]:
                imm=self.imm(tokens[1],lineno)
                self.emit32(self.encode_I(opcode,0,0,imm))

            elif op=="LDI":
                d=self.reg(tokens[1],lineno)
                imm=self.imm(tokens[2],lineno)
                self.emit32(self.encode_I(opcode,d,0,imm))

            elif op=="PUSHI":
                imm=self.imm(tokens[1],lineno)
                self.emit32(self.encode_I(opcode,0,0,imm))

            elif op=="JRI":
                target=tokens[1]
                if target in self.symbols:
                    offset=self.symbols[target]-self.pc
                else:
                    offset=self.imm(target,lineno)
                self.emit32(self.encode_I(opcode,0,0,offset))

            elif op in ["SHL","SHR"]:
                d=self.reg(tokens[1],lineno)
                s=self.reg(tokens[2],lineno)
                imm=self.imm(tokens[3],lineno)
                self.emit32(self.encode_I(opcode,d,s,imm))

            elif op=="LEA":
                d=self.reg(tokens[1],lineno)
                s=self.reg(tokens[2],lineno)
                imm=self.imm(tokens[3],lineno)
                self.emit32(self.encode_I(opcode,d,s,imm))

            elif op=="STI":
                d=self.reg(tokens[1],lineno)
                imm=self.imm(tokens[2],lineno)
                self.emit32(self.encode_I(opcode,d,0,imm))

    def assemble(self,text):
        self.load(text)
        self.pass1()
        self.pass2()
        return self.output


if __name__=="__main__":
    asm=Assembler()

    with open(sys.argv[1],"r") as f:
        code=f.read()

    binary=asm.assemble(code)

    out=sys.argv[1]+".bin"

    with open(out,"wb") as f:
        f.write(binary)

    print(f"Assembled code written to {out}")
