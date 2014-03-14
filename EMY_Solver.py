# EMY Solver
# Workflow :
#   Registers, instructions in pipeline.
#   Dependencies between instructions, output tables
#   Currently implementing v2: Int + FP pipeline

class Register:
	def __init__(self,name):
		self.name = name
	
class Instruction:
	def __init__(self,opcode,instr):
		self.i = instr
		self.opcode = opcode
		# Src & output regs
		self.rs = None
		self.ro = None
		self.latency = 1
		# Define stages
		self.IF = None
		self.ID = None
		self.EX = None
		self.MEM = None
		self.CM = None

	def compute_regs(self,regs):
		oc = self.opcode
		line = regs.split(', ')
		self.ro = line[0]
		
		# loads
		if oc in ['L.D','LD','SD','S.D']:
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
	
	for instr in i_list:
		print instr.i,'\t',instr.IF,'\t',instr.ID,'\t',

		if instr.EX:
			if len(instr.EX) == 3:
				print "%s/%s-%s"%(instr.EX[2],instr.EX[0],instr.EX[1]),
			elif instr.EX[0] == instr.EX[1]:
				print instr.EX[0],
			else:
				print "%s-%s"%instr.EX,

		if instr.MEM:
			print '\t',instr.MEM,

		if instr.CM:
			print '\t',instr.CM
		else:
			print

# Find dependencies and return delays if any
def find_dependencies(current_instr,instr_seen):

	# result = [instr for instr in instr_seen if instr.ro in current_instr.rs]
	result = []
	for instr in instr_seen:
		if instr.ro and instr.ro in current_instr.rs:
			result.append(instr)
	return result


def fill_pipeline(i_list):
	pc         = 0
	clk        = 1
	instr_seen = []
	
	while pc < len(i_list):
		# Check for dependencies
		dependency = find_dependencies(i_list[pc],instr_seen)		
		instr_seen.append(i_list[pc])

		i_list[pc].IF   = clk
		i_list[pc].ID   = clk + 1
		i_list[pc].EX   = (i_list[pc].ID + 1,i_list[pc].ID + i_list[pc].latency)

		# Handle EX
		if dependency:
			tmp = []
			for instr in dependency:
				if instr.opcode in ['LD','L.D']	and instr.CM > i_list[pc].EX[0]:
					tmp.append((instr.CM,
											instr.CM + i_list[pc].latency,
											i_list[pc].EX[0]))
				if instr.opcode in ['MUL.D','ADD.D','SUB.D','DIV.D','DADDI'] \
					and instr.MEM > i_list[pc].EX[0]:
					tmp.append((instr.MEM,
											instr.MEM + i_list[pc].latency,
											i_list[pc].EX[0]))        
			# Replace with itemgetter from operator
			if tmp:
				i_list[pc].EX = max(tmp, key = lambda item:item[0])
				stall = 'EX'
		
		i_list[pc].MEM  = i_list[pc].EX[1] + 1

		# Handle SD/S.D
		if i_list[pc].opcode in ['SD','S.D']:
			i_list[pc].CM = None
		else:
			i_list[pc].CM = i_list[pc].MEM + 1

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
