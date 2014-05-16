#Load in an ASF file for a skeleton description
#http://research.cs.wisc.edu/graphics/Courses/cs-838-1999/Jeff/ASF-AMC.html
#Motion capture data found in the CMU MOCAP database
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
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
		self.initialRotMatrix = None
	
	def finishInit(self):
		#Precompute Rotation matrix
		angles = [float(a)*np.pi/180.0 for a in self.orientation]
		self.initialRotMatrix = getRotationMatrix(angles[0], angles[1], angles[2], {"rx": 0, "ry": 1, "rz": 2})

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
		self.initialRotMatrix = None

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
			if fields[0][0] in ['#', '\0'] or len(fields[0]) == 0:
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
					self.root.finishInit()
					parseState = Skeleton.PARSE_BONEDATA
				else:
					#print "ROOT FIELD: |%s|"%fields[0]
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
				#print "BONE FIELD: |%s|"%fields[0]
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
		self.boneMatrices = {}
		self.NStates = 0
	
	def initMatrices(self, bone, level, index, matrix):
		[rx, ry, rz] = [0]*3
		if "rx" in bone.dof:
			rx = self.bonesStates[bone.name][index][bone.dof["rx"]]*np.pi/180
		if "ry" in bone.dof:
			ry = self.bonesStates[bone.name][index][bone.dof["ry"]]*np.pi/180
		if "rz" in bone.dof:
			rz = self.bonesStates[bone.name][index][bone.dof["rz"]]*np.pi/180
		rotMatrix = getRotationMatrix(rx, ry, rz, bone.dof)
		rotMatrixInv = rotMatrix.transpose()
		pos = [bone.length*a for a in bone.direction]
		translationMatrix = np.eye(4)
		translationMatrix[0:3, 3] = np.array([pos[0], pos[1], pos[2]])
		nextMatrix = rotMatrix.dot(translationMatrix.dot(rotMatrixInv))
		matrix = matrix.dot(nextMatrix)
		self.boneMatrices[bone.name].append(matrix)
		for child in bone.children:
			self.initMatrices(child, level+1, index, matrix)
	
	def initFromFile(self, filename):
		print "Initializing..."
		for bone in self.skeleton.bones:
			self.bonesStates[bone] = []
		#Step 1: Load in states from file
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
		#Step 2: Initialize matrices
		for bone in self.bonesStates:
			self.boneMatrices[bone] = []
		for index in range(self.NStates):
			#First initialize the root matrix
			bone = self.skeleton.bones['root']
			[TX, TY, TZ, RX, RY, RZ] = [0]*6
			rotorder = bone.order.copy()
			if "TX" in bone.order:
				TX = self.bonesStates[bone.name][index][bone.order["TX"]]
			if "TY" in bone.order:
				TY = self.bonesStates[bone.name][index][bone.order["TY"]]
			if "TZ" in bone.order:
				TZ = self.bonesStates[bone.name][index][bone.order["TZ"]]
			if "RX" in bone.order:
				RX = self.bonesStates[bone.name][index][bone.order["RX"]]*np.pi/180
				rotorder["RX"] = rotorder["RX"] - 3
			if "RY" in bone.order:
				RY = self.bonesStates[bone.name][index][bone.order["RY"]]*np.pi/180
				rotorder["RY"] = rotorder["RY"] - 3
			if "RZ" in bone.order:
				RZ = self.bonesStates[bone.name][index][bone.order["RZ"]]*np.pi/180
				rotorder["RZ"] = rotorder["RZ"] - 3
			translationMatrix = np.eye(4)
			translationMatrix[0:3, 3] = np.array([TX, TY, TZ])
			rotMatrix = getRotationMatrix(RX, RY, RZ, rotorder)
			matrix = translationMatrix.dot(rotMatrix)
			self.boneMatrices['root'].append(matrix)
			for child in bone.children:
				self.initMatrices(child, 1, index, matrix)
		print "Finished initializing"
	
	def renderNode(self, bone, parent, level, index):
		if index >= self.NStates:
			return
		#Endpoint are always matrix[0:3, 3]
		P1 = self.boneMatrices[parent.name][index][0:3, 3]
		P2 = self.boneMatrices[bone.name][index][0:3, 3]
		colors = [ [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1] ]
		C = colors[bone.id%len(colors)]
		glColor3f(C[0], C[1], C[2])
		
		glPointSize(20)
		glBegin(GL_POINTS)
		glVertex3f(P1[0], P1[1], P1[2])
		glEnd()
		
		glLineWidth(10)
		glBegin(GL_LINES)
		glVertex3f(P1[0], P1[1], P1[2])
		glVertex3f(P2[0], P2[1], P2[2])
		glEnd()
		
		for child in bone.children:
			self.renderNode(child, bone, level+1, index)
	
	def renderState(self, index):
		root = self.skeleton.bones['root']
		for child in root.children:
			self.renderNode(child, root, 1, index)
	
	def getBBox(self):
		matrices = self.boneMatrices['root']
		xmin = matrices[0][0, 3]
		xmax = matrices[0][0, 3]
		ymin = matrices[0][1, 3]
		ymax = matrices[0][1, 3]
		zmin = matrices[0][2, 3]
		zmax = matrices[0][2, 3]
		for matrix in matrices:
			xmin = min(matrix[0, 3], xmin)
			xmax = max(matrix[0, 3], xmax)
			ymin = min(matrix[1, 3], ymin)
			ymax = max(matrix[1, 3], ymax)
			zmin = min(matrix[2, 3], zmin)
			zmax = max(matrix[2, 3], zmax)
		return [xmin, xmax, ymin, ymax, zmin, zmax]

if __name__ == '__main__':
	skeleton = Skeleton()
	skeleton.initFromFile("test.asf")
	activity = SkeletonAnimator(skeleton)
	activity.initFromFile("test.amc")
