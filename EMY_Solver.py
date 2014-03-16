# EMY Solver
# Workflow :
#   Registers, instructions in pipeline.
#   Dependencies between instructions, output tables
#   Currently implementing v2: Int + FP pipeline

class Register:
    def __init__(self,name):
        self.name = name

class Stage:
    def __init__(self):
        self.stall = None
        self.start = None
        self.end = None

    def __str__(self):
        if self.end:
            if self.stall:
                return "%s/%s-%s" %(self.start,self.stall,self.end)
            else:
                if self.start != self.end:
                    return "%s-%s" %(self.start,self.end)
                else:
                    return "%s" %self.start
        else:
            if self.stall:
                return "%s/%s" %(self.start,self.stall)
            else:
                return "%s" %self.start

    
class Instruction:
    def __init__(self,opcode,instr):
        self.i = instr
        self.opcode = opcode
        # Src & output regs
        self.rs = None
        self.ro = None
        self.latency = 1
        # Define stages
        self.IF = Stage()
        self.ID = Stage()
        self.EX = Stage()
        self.MEM = Stage()
        self.CM = Stage()

    def compute_regs(self,regs):
        oc = self.opcode
        line = regs.split(', ')
        self.ro = line[0]
        
        # loads
        if oc in ['L.D','LD']:
            self.rs = [line[1].split('(')[1][:-1]]

        # stores
        if oc in ['SD','S.D']:
            self.r_mem = line[0]
            self.rs = line[1].split('(')[1][:-1]
            
        # calculations
        if oc in ['MUL.D','ADD.D','SUB.D','DIV.D']:
            self.latency = 3
            self.rs = list(set(line[1:]))

        # immediate calculations
        if oc in ['DADDI','MULDI']:
            self.rs = line[1]
            
        # branches
        if oc in ['BNEZ']:
            self.rs = self.ro
            self.ro = None

def create_instructions(data):
    i_list = []
    for instr in data:
        instr = instr.strip()
        oc, regs = instr.split('\t')
        i = Instruction(oc,instr)
        i.compute_regs(regs)
        i_list.append(i)
        
    return i_list

def display(i_list):
    print """			IF	ID	EX	MEM	CM
==========================================================="""
    for instr in i_list:
        print instr.i,'\t',instr.IF,'\t',instr.ID,'\t',

        if instr.EX:
            print instr.EX,

        if instr.MEM:
            print '\t',instr.MEM,

        if instr.CM:
            print '\t',instr.CM,
        
        print

# Find dependencies and return delays if any
def find_dependencies(current_instr,instr_seen):
    # return [instr for instr in instr_seen if instr.ro in current_instr.rs]
    result = []
    for instr in instr_seen:
        if instr.ro and instr.ro in current_instr.rs:
            result.append(instr)
    return result

def find_mem_dep(instr,instr_seen):
    max = 0
    for i in instr_seen:
        if i.ro and i.ro in instr.r_mem and i.MEM.start > instr.MEM.start:
            if i.MEM.start > max:
                max = i.MEM.start
    return max


def fill_pipeline(i_list):
    pc         = 0
    clk        = 1
    instr_seen = []
    stall      = None
    bubble     = None
    
    while pc < len(i_list):
        # Check for dependencies
        dependency = find_dependencies(i_list[pc],instr_seen)
        instr_seen.append(i_list[pc])

        # Handle IF
        if bubble == '_IF':
            clk     = i_list[pc-1].ID.start
            bubble  = None

        i_list[pc].IF.start = clk 
            
        if stall == 'IF':
            i_list[pc].IF.stall   = i_list[pc-1].ID.stall
            bubble                = '_IF'   # Final bubble
            stall                 = None

        # Handle ID
        i_list[pc].ID.start = (i_list[pc].IF.stall if i_list[pc].IF.stall else i_list[pc].IF.start)+1
        if stall == 'ID':
             i_list[pc].ID.stall  = i_list[pc-1].EX.stall
             stall                = 'IF'
                    
        i_list[pc].EX.start = (i_list[pc].ID.stall if i_list[pc].ID.stall else i_list[pc].ID.start)+1

        # Handle EX
        if dependency and i_list[pc].opcode != 'S.D':
            max_stall = 0
            for instr in dependency:
                if instr.opcode in ['LD','L.D'] and instr.CM.start >= i_list[pc].EX.start:
                    if instr.CM.start > max_stall:
                        max_stall = instr.CM.start
                if instr.opcode in ['MUL.D','ADD.D','SUB.D','DIV.D','DADDI']:
                    if instr.MEM.start >= i_list[pc].EX.start:
                        if instr.MEM.start > max_stall:
                            max_stall = instr.MEM.start
                    elif instr.CM.start >= i_list[pc].EX.start:
                        if instr.CM.start > max_stall:
                            max_stall = instr.CM.start                    
            # Replace with itemgetter from operator
            if max_stall and max_stall != i_list[pc].EX.start:
                i_list[pc].EX.stall = max_stall
                stall               = 'ID'
        
        i_list[pc].EX.end = (i_list[pc].EX.stall if i_list[pc].EX.stall else i_list[pc].EX.start) + i_list[pc].latency - 1

        # Handle MEM
        i_list[pc].MEM.start  = i_list[pc].EX.end + 1
        if i_list[pc].opcode == 'S.D':
            i_list[pc].MEM.start  = find_mem_dep(i_list[pc],instr_seen)
            i_list[pc].EX.start = i_list[pc].MEM.start - 1
            i_list[pc].EX.end = i_list[pc].EX.start
            i_list[pc].ID.stall = i_list[pc].EX.start - 1

        # Handle CM with SD/S.D
        if i_list[pc].opcode in ['SD','S.D']:
            i_list[pc].CM = None
        else:
            i_list[pc].CM.start = i_list[pc].MEM.start + 1

        # Handle BNEZ
        if i_list[pc].opcode == 'BNEZ':
            i_list[pc].EX = i_list[pc].MEM = i_list[pc].CM = None 

        clk += 1
        pc += 1

def main():
    # Assumption, code is always valid
    with open('input.txt','r') as f:
        data = f.readlines()
        
    i_list = create_instructions(data)
    fill_pipeline(i_list)
    display(i_list)
    

# Entry
main()
