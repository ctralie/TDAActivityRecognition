#Load in an ASF file for a skeleton description
#http://research.cs.wisc.edu/graphics/Courses/cs-838-1999/Jeff/ASF-AMC.html
#Motion capture data found in the CMU MOCAP database
from Primitives3D import *

class SkeletonRoot(object):
	def __init__(self):
		self.axis = "XYZ"
		self.order = "TX TY TZ RZ RY RX"
		self.position = Point3D(0, 0, 0)
		self.orientation = [0, 0, 0]
		self.children = []

class SkeletonBone(object):
	def __init__(self):
		self.name = "NONAME"
		self.id = -1
		self.direction = [0, 0, 0]
		self.axis = [0, 0, 0]
		self.length = 0.0
		self.dof = []
		self.limits = []
		self.children = []

class Skeleton(object):
	(PARSE_DEFAULT, PARSE_UNITS, PARSE_DOCUMENTATION, PARSE_ROOT, PARSE_BONEDATA, PARSE_BONEDATALIMITS, PARSE_HIERARCHY, PARSE_FINISHED) = (0, 1, 2, 3, 4, 5, 6, 7)

	def __init__(self):
		self.version = "1.0"
		self.units = []
		self.documentation = []
		self.root = SkeletonRoot()
		self.bones = {'root':self.root}
	
	def initFromFile(self, filename):
		fin = open(filename, 'r')
		lineCount = 0
		parseState = Skeleton.PARSE_DEFAULT
		thisBone = None
		for line in fin:
			lineCount = lineCount + 1
			fields = ((line.lstrip()).rstrip()).split() #Splits whitespace by default
			if len(fields) == 0: 
				continue #Blank line
			if fields[0][0] in ['#', '\0', 'o'] or len(fields[0]) == 0:
				continue #Comments and stuff
			if parseState == Skeleton.PARSE_DEFAULT:
				if fields[0] == ":version":
					self.version = fields[1]
				elif fields[0] == ":name":
					self.name = fields[1]
				elif fields[0] == ":units":
					parseState = Skeleton.PARSE_UNITS
				else:
					print "Unexpected line while in PARSE_DEFAULT: %s"%line
			elif parseState == Skeleton.PARSE_UNITS:
				if fields[0] == ":documentation":
					parseState = Skeleton.PARSE_DOCUMENTATION
				elif fields[0] == ":root":
					parseState = Skeleton.PARSE_ROOT
				elif fields[0] == ":bonedata":
					parseState = Skaleton.PARSE_BONEDATA
				else:
					self.units.append(line)
			elif parseState == Skeleton.PARSE_DOCUMENTATION:
				if fields[0] == ":root":
					parseState = Skeleton.PARSE_ROOT
				elif fields[0] == ":bonedata":
					parseState = Skeleton.PARSE_BONEDATA
				else:
					self.documentation.append(line)
			elif parseState == Skeleton.PARSE_ROOT:
				if fields[0] == ":bonedata":
					parseState = Skeleton.PARSE_BONEDATA
				else:
					if fields[0] == "axis":
						self.root.axis = fields[1]
					elif fields[0] == "order":
						orderstr = line.split("order")[1].lstrip()
						self.root.order = orderstr
					elif fields[0] == "position":
						point = [float(x) for x in fields[1:]]
						self.root.position = Point3D(point[0], point[1], point[2])
					elif fields[0] == "orientation":
						orientation = [float(x) for x in fields[1:]]
						self.root.orientation = orientation
					else:
						print "Warning: unrecognized field %s in root"%fields[0]
			elif parseState == Skeleton.PARSE_BONEDATA:
				if fields[0] == "begin":
					thisBone = SkeletonBone()
				elif fields[0] == "end":
					self.bones[thisBone.name] = thisBone
				elif fields[0] == "name":
					thisBone.name = fields[1]
				elif fields[0] == "id":
					thisBone.id = int(fields[1])
				elif fields[0] == "direction":
					direction = [float(x) for x in fields[1:]]
					thisBone.direction = direction
				elif fields[0] == "length":
					thisBone.length = float(fields[1])
				elif fields[0] == "axis":
					axis = [float(x) for x in fields[1:4]]
					thisBone.axis = axis
				elif fields[0] == "dof":
					dof = [x.lstrip().rstrip() for x in fields[1:]]
					thisBone.dof = dof
				elif fields[0] == "limits":
					parseState = Skeleton.PARSE_BONEDATALIMITS
					limits = line.split("(")[1]
					limits = limits.split(")")[0]
					limits = [float(x) for x in limits.split()]
					thisBone.limits.append(limits)
				elif fields[0] == ":hierarchy":
					parseState = Skeleton.PARSE_HIERARCHY
			elif parseState == Skeleton.PARSE_BONEDATALIMITS:
				if fields[0] == "end":
					self.bones[thisBone.name] = thisBone
					parseState = Skeleton.PARSE_BONEDATA
				else:
					limits = line.split("(")[1]
					limits = limits.split(")")[0]
					limits = [float(x) for x in limits.split()]
					thisBone.limits.append(limits)
			elif parseState == Skeleton.PARSE_HIERARCHY:
				if len(fields) == 1 and fields[0] == "begin":
					parseState = Skeleton.PARSE_HIERARCHY
				elif len(fields) == 1 and fields[0] == "end":
					parseState = Skeleton.PARSE_FINISHED
				else:
					parent = fields[0]
					children = fields[1:]
					self.bones[parent].children = [self.bones[s] for s in children]
			elif parseState == Skeleton.PARSE_FINISHED:
				print "Warning: Finished, but got line %s"%line
		fin.close()

if __name__ == '__main__':
	skeleton = Skeleton()
	skeleton.initFromFile("test.asf")
