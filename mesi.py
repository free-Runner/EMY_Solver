# mesi.py
# Simple implemetation of MESI cache coherence (Illinois cache protocol)
# based on: http://en.wikipedia.org/wiki/File:MESI_protocol_activity_diagram.png

# States
# M : Modified
# E : Exclusive
# S : Shared
# I : Invalid
m,e,s,i = range(4)	# simple enum hack

class P:
	""" 
	Processor Class 
	@ p		: static master list of processors
	@ read 	: read an element from cache
	@ write : write to element in cache
	"""
	p   = []

	def __init__(self):
		"""
		@ state : hold current mesi value, default to i
		@ elem  : hold memory block name, None when state is i
		"""
		P.p.append(self)	# add to static list
		self.state = i
		self.elem  = None

	def __repr__(self):
		return dict(zip(range(4),'mesi')).get(self.state)

	def find_elem(self,elem):
		return [x for x in P.p if (elem==x.elem and x is not self)]

	def read_miss(self):
		copies = self.find_elem(self.elem)
		num    = len(copies)
		if num == 0:					# get from mem
			self.state = e
		elif num == 1:					# get from peer
			if copies[0].state == e:
				pass	#log exclusive
			elif copies[0].state == m:
				pass	#log mod

			copies[0].state = s
			self.state = s
		else:							# join shared
			self.state = s

	def read(self,elem):
		if self.elem == elem and self.state != i:
			pass		# hit - No change of state
		else:
			# miss
			if self.elem:
				pass		# log write to mem

			self.elem = elem
			self.read_miss()

	def invalidate_others(self,others):
		for processor in others:
			processor.state = i
			processor.elem  = None

	def write_hit(self):
		if self.state == m:
			pass
		elif self.state == e:
			pass
		else:
			# no longer shared
			others = self.find_elem(self.elem)
			self.invalidate_others(others)

	def write_miss(self):
		copies = self.find_elem(self.elem)
		# no copies no problem
		if not copies:
			return

		if len(copies) == 1 and copies[0].state == m:
			# log
			pass
		
		self.invalidate_others(copies)

	def write(self,elem):
		if self.elem == elem and self.state != i:
			# hit
			self.write_hit()
		else:
			# miss
			if self.elem:
				pass		#log
			self.elem = elem
			self.write_miss()

		self.state = m

if __name__ == "__main__":
	# Test code goes here
	a = P()
	b = P()
	r = P.read
	w = P.write
	k = 'k'
	r(a,k)
	r(b,k)

	print P.p