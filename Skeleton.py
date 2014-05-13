#Load in an ASF file for a skeleton description
#http://research.cs.wisc.edu/graphics/Courses/cs-838-1999/Jeff/ASF-AMC.html
#Motion capture data found in the CMU MOCAP database
from OpenGL.GL import *
import numpy as np

def getRotationMatrix(rx, ry, rz, order):
	rotX = np.eye(4)
	rotX[1, 1] = np.cos(rx)
	rotX[2, 1] = np.sin(rx)
	rotX[1, 2] = -np.sin(rx)
	rotX[2, 2] = np.cos(rx)
	rotY = np.eye(4)
	rotY[0, 0] = np.cos(ry)
	rotY[2, 0] = np.sin(ry)
	rotY[0, 2] = -np.sin(ry)
	rotY[2, 2] = np.cos(ry)
	rotZ = np.eye(4)
	rotZ[0, 0] = np.cos(rz)
	rotZ[1, 0] = np.sin(rz)
	rotZ[0, 1] = -np.sin(rz)
	rotZ[1, 1] = np.cos(rz)
	matrices = [np.eye(4), np.eye(4), np.eye(4)]
	for matrixType in order:
		if matrixType.lower() == "rx":
			matrices[order[matrixType]] = rotX
		elif matrixType.lower() == "ry":
			matrices[order[matrixType]] = rotY
		elif matrixType.lower() == "rz":
			matrices[order[matrixType]] = rotZ
	return matrices[2].dot(matrices[1].dot(matrices[0]))

class SkeletonRoot(object):
	def __init__(self):
		self.id = -1
		self.name = "root"
		self.axis = "XYZ"
		self.order = {}
		self.position = [0, 0, 0]
		self.orientation = [0, 0, 0]
		self.children = []

class SkeletonBone(object):
	def __init__(self):
		self.name = "NONAME"
		self.id = -1
		self.direction = [0, 0, 0]
		self.axis = [0, 0, 0]
		self.length = 0.0
		self.dof = {}
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
						ordervals = orderstr.split()
						for i in range(len(ordervals)):
							self.root.order[ordervals[i].lstrip().rstrip()] = i
					elif fields[0] == "position":
						point = [float(x) for x in fields[1:]]
						self.root.position = point
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
					dof = [(x.lstrip().rstrip()).lower() for x in fields[1:]]
					for i in range(0, len(dof)):
						thisBone.dof[dof[i]] = i
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

class SkeletonAnimator(object):
	def __init__(self, skeleton):
		self.skeleton = skeleton
		self.bonesStates = {}
		self.NStates = 0
	
	def initFromFile(self, filename):
		for bone in self.skeleton.bones:
			self.bonesStates[bone] = []
		fin = open(filename, 'r')
		lineCount = 0
		for line in fin:
			lineCount = lineCount + 1
			fields = ((line.lstrip()).rstrip()).split() #Splits whitespace by default	
			if len(fields) == 0: 
				continue #Blank line
			if fields[0][0] in ['#', '\0', 'o'] or len(fields[0]) == 0:
				continue #Comments and stuff
			if fields[0] == ":FULLY-SPECIFIED":
				continue
			if fields[0] == ":DEGREES":
				continue
			if len(fields) == 1:
				continue #The number of the frame, but I don't need to explicitly store this
			bone = fields[0]
			values = [float(a) for a in fields[1:]]
			self.bonesStates[bone].append(values)	
		self.NStates = max([len(self.bonesStates[bone]) for bone in self.bonesStates])			
		fin.close()
	
	def renderNode(self, bone, level, index):
		if index >= self.NStates:
			return;
		colors = [ [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1] ]
		C = colors[bone.id%len(colors)]
		glColor3f(C[0], C[1], C[2])
		glPushMatrix()
		if bone.name == "root":
			[TX, TY, TZ, RX, RY, RZ] = [0]*6
			if "TX" in bone.order:
				TX = self.bonesStates[bone.name][index][bone.order["TX"]]
			if "TY" in bone.order:
				TY = self.bonesStates[bone.name][index][bone.order["TY"]]
			if "TZ" in bone.order:
				TZ = self.bonesStates[bone.name][index][bone.order["TZ"]]
			if "RX" in bone.order:
				RX = self.bonesStates[bone.name][index][bone.order["RX"]]*np.pi/180
			if "RY" in bone.order:
				RY = self.bonesStates[bone.name][index][bone.order["RY"]]*np.pi/180
			if "RZ" in bone.order:
				RZ = self.bonesStates[bone.name][index][bone.order["RZ"]]*np.pi/180
			rotMatrix = getRotationMatrix(RX, RY, RZ, bone.order)
			glMultMatrixd(rotMatrix.transpose().flatten())
			glTranslatef(TX, TY, TZ)
		else:
			[rx, ry, rz] = [0]*3
			if "rx" in bone.dof:
				rx = self.bonesStates[bone.name][index][bone.dof["rx"]]*np.pi/180
			if "ry" in bone.dof:
				ry = self.bonesStates[bone.name][index][bone.dof["ry"]]*np.pi/180
			if "rz" in bone.dof:
				rz = self.bonesStates[bone.name][index][bone.dof["rz"]]*np.pi/180
			rotMatrix = getRotationMatrix(rx, ry, rz, bone.dof)
			glMultMatrixd(rotMatrix.transpose().flatten())
			glPointSize(5)
			glVertex3f(0, 0, 0)
			glLineWidth(5)
			glBegin(GL_LINES)
			glVertex3f(0, 0, 0)
			glVertex3f(bone.length, 0, 0)
			glEnd()
			glTranslatef(bone.length, 0, 0)
		for child in bone.children:
			self.renderNode(child, level+1, index)
		glPopMatrix()
	
	def renderState(self, index):
		self.renderNode(self.skeleton.bones['root'], 0, index)
		

if __name__ == '__main__':
	skeleton = Skeleton()
	skeleton.initFromFile("test.asf")
	activity = SkeletonAnimator(skeleton)
	activity.initFromFile("test.amc")
