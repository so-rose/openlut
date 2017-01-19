#!/usr/bin/env python3

'''
Copyright 2016 Sofus Rose

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

import sys, os, time
import multiprocessing as mp

class Files :
	"""
	The Files object is an immutable sequence of files, which supports writing simultaneously to all the files.
	"""
	def __init__(self, *files) :
		seq=[]
		for f in files:
			if isinstance(f, Files): seq += f.files
			elif 'write' in dir(f): seq.append(f)
			else: raise TypeError('Wrong Input Type: ' + repr(f))

		self.files = tuple(seq) #Immutable tuple of file-like objects,



	def write(self, inStr, exclInd=[]) :
		"""
		Writes inStr all file-like objects stored within the Files object. You may exclude certain entries with a sequence of indices.
		"""
		for f in enumerate(self.files) :
			if f[0] in exclInd: continue
			f[1].write(inStr)




	def __add__(self, o, commut=False) :
		"""
		Implements merging with Files objects and appending file-like objects. Returns new Files object.
		"""
		if isinstance(o, Files) :
			this, other = self.files, o.files
		elif 'write' in dir(o) :
			this, other = self.files, [o]
		else :
			return None

		if commut: this, other = other, this

		return Files(*this, *other) #this and other must be unpackable.

	def __radd__(self, o) :
		"""
		Commutative addition.
		"""
		return self.__add__(o, commut=True) #Use the add operator. It's commutative!!

	def __bool__(self) :
		"""
		False if empty.
		"""
		return bool(self.files)



	def __getitem__(self, index) :
		"""
		Supports slicing and indexing.
		"""
		if isinstance(index, slice) :
			return Files(self.files[index])
		else :
			return self.files[index]

	def __len__(self) :
		"""
		Number of files in the Files object.
		"""
		return len(self.files)

	def __repr__(self) :
		return 'Files(' + ', '.join("'{}'".format(n.name) for n in self.files) + ')'

	def __iter__(self) :
		"""
		Iterates through the file-like objects.
		"""
		return iter(self.files)

class ColLib :
	"""
	Simple hashmap to colors.. Make sure to activate colors in ~/.bashrc or enable ansi.sys!
	"""
	cols = {	'HEADER' : '\033[97m',
				'OKBLUE' : '\033[94m',
				'OKGREEN' : '\033[92m',
				'WARNING' : '\033[93m',
				'FAIL' : '\033[91m',
				'CRIT' : '\033[31m',
				'DEBUG' : '\033[35m',

				'ENDC' : '\033[0m',

				'BOLD' : '\033[1m',
				'ITALIC' : '\033[3m',
				'UNDERLINE' : '\033[4m'
	}



	debug = {	'info' : ('[INFO]', 'OKGREEN'),
				'error' : ('[ERROR]', 'FAIL'),
				'crit' : ('[CRIT]', 'CRIT'),
				'warn' : ('[WARNING]', 'WARNING'),
				'debug' : ('[DEBUG]', 'DEBUG'),
				'run' : ('[RUN]', 'OKBLUE')
	}



	def colString(color, string) :
		"""
		Returns a colored string.
		"""
		return '{}{}{}'.format(cols[color], string, cols['ENDC'])

	def dbgString(signal, string) :
		"""
		"""
		return '{}{}{}'.format(debug[signal])



	def printCol(color, colored, *output, **settings) :
		"""
		Simple print clone where the first printed parameter is colored.
		"""
		print(cols[color] + str(colored) + cols['ENDC'], *output, **settings)

	def printDbg(signal, *output, **settings) :
		"""
		Pass in simple debug signals to print the corresponding entry.
		"""
		printCol(debug[signal][1], debug[signal][0] + ' ' + colored, *output, **settings)

class Log(ColLib) :
	"""
	Logging object, an instance of which is passed throughout afarm. **It has + changes state**, as the sole exception to the
	'no globals' paradigm. You may pass in any file-like object, the only criteria being that it has a 'write' method. stdout is
	used by default.
	"""
	def __init__(self, *file, verb=3, useCol=True, startTime=None) :
		if not file: file = [sys.stdout]
		if startTime is None: startTime = time.perf_counter()

		self.verb = verb #From 0 to 3. 0: CRITICAL 1: ERRORS 2: WARNINGS 3: DEBUG. Info all.
		self.file = Files(*file)

		self.log = [] #Log list. Format: (verb, time in ms, debug_text, text)
		self.sTimes = dict() #Dict of start times for various runs.
		
		self._useCol = useCol #Whether or not to use colored output.
		self._attrLock = mp.Lock() #The log access lock.
		self._startTime = startTime #Global instance time. begins when the instance is created.



	def getLogTime(self) :
		"""
		Gets the current logging time in seconds, from the time of instantiation of the Log object.
		"""
		return time.perf_counter() - self._startTime
		
	def startTime(self, run) :
		"""
		Starts the timer for the specified run. Can use any immutable object to mark the run.
		"""
		self.sTimes[run] = self.getLogTime()
		
	def getTime(self, run) :
		"""
		Gets the time since startTime for the specified run (an immutable object).
		"""
		if run in self.sTimes :
			return self.getLogTime() - self.sTimes[run]
		else :
			raise ValueError('Run wasn\'t found!!')

	def compItem(self, state, time, *text) :
		"""
		Returns a displayable log item as a string, formatted with or without color.
		"""
		decor = {	'info' : '',
					'error' : '',
					'crit' : ColLib.cols['BOLD'],
					'warn' : '',
					'debug' : ColLib.cols['BOLD'],
					'run' : ColLib.cols['BOLD']
		}[state]
				
		timeCol = {	'info' : ColLib.cols['HEADER'],
					'error' : ColLib.cols['WARNING'],
					'crit' : ColLib.cols['FAIL'],
					'warn' : ColLib.cols['HEADER'],
					'debug' : ColLib.cols['DEBUG'] + ColLib.cols['BOLD'],
					'run' : ColLib.cols['OKGREEN']
		}[state]
						
		if self._useCol :
			return '{3}{5}{0}{4[ENDC]}\t{6}{1:.10f}{4[ENDC]}: {2}'.format(	ColLib.debug[state][0],
																				time,
																				''.join(text),
																				ColLib.cols[ColLib.debug[state][1]],
																				ColLib.cols,
																				decor,
																				timeCol
																		)
		else :
			return '{0} {1:.10f}: {2}'.format(ColLib.debug[state][0], time, ''.join(text))



	def write(self, *text, verb=2, state='info') :
		"""
		Adds an entry to the log file, as well as to the internal structure.

		Possible state values:
		*'info': To give information.
		*'error': When things go wrong.
		*'crit': When things go very wrong.
		*'warn': To let the user know that something weird is up.
		*'run': To report on an intensive process.
		*'debug': For debugging purposes. Keep it at verbosity 3.
		
		Possible verbosity values, and suggested usage:
		*0: User-oriented, general info about important happenings.
		*1: Helpful info about what is running/happening, even to the user.
		*2: Deeper info about the programs functionality, for fixing problems.
		*3: Developer oriented debugging.
		"""
		text = [str(t).strip() for t in text if str(t).strip()]
		if not text: return #Empty write's are no good.
		curTime = self.getLogTime()
		with self._attrLock :
			self.log.append( {	'verb' 	: verb,
								'time' 	: curTime,
								'state'	: state,
								'text'	: ' '.join(str(t) for t in text)
							}
			)

		if self.verb >= verb :
			with self._attrLock :
				print(self.compItem(state, curTime, ' '.join(text)), file=self.file)

	def read(self, verb=None) :
		"""
		Reads the internal logging data structure, optionally overriding verbosity.
		"""
		if not verb: verb = self.verb
		with self._attrLock :
			return '\n'.join([self.compItem(l['state'], l['time'], l['text']) for l in self.log if verb >= l['verb']])

	def reset(self, startTime=None) :
		return Log(self.file, verb=self.verb, useCol=self._useCol, startTime=startTime)



	def getFiles(self) :
		"""
		Get the list of files to dump Log output to.
		"""
		return self.file

	def setFiles(self, *files) :
		"""
		Set a new list of files to dump Log output to.
		"""
		with self._attrLock :
			self.file = Files(*files)

	def addFiles(self, *files) :
		"""
		Add a list of files to dump Log output to.
		"""
		with self._attrLock :
			self.file += Files(*files)



	def setVerb(self, newVerb) :
		"""
		Call to set verbosity.
		"""
		with self._attrLock :
			self.verb = newVerb
		self.write('Verbosity set to', str(newVerb) + '.', verb=0, state='info')

	def setCol(self, newUseCol) :
		"""
		Call to change color output.
		"""
		with self._attrLock :
			self._useCol = newUseCol
		self.write('Color Output set to', self._useCol, verb=0, state='info')



	def __call__(self, verb, state, *text) :
		"""
		Identical to Log.write(), except it requires the verbosity level to be specified.
		"""
		self.write(verb=verb, state=state, *text)

	def __repr__(self) :
		return (	'Log(' +
					(', '.join("'{}'".format(f.name) for f in self.file.files) + ', ' if self.file else '') +
					'verb={}, useCol={}, startTime={:.3f})'.format(self.verb, self._useCol, self._startTime)
			)

	def __str__(self) :
		return self.read()



	def __add__(self, o, commut=False) :
		"""
		Merges a Log object with another Log object, a Files object, or a file-like object.
		*For Log object addition, the minimum startTime attibute is used to initialize the merged startTime.
		*The Files objects of both Log objects are merged.
		"""

		if isinstance(o, Log) :
			l = self.reset(min(self.getLogTime(), o.getLogTime())) #Max of self and other time.
			l.log = self.log + o.log
			l.log.sort(key=lambda item: item['time']) #Make sure to sort the internal log by time.
			l.addFiles(o.file)
			return l
		elif isinstance(o, Files) :
			l = self.reset(self.getLogTime())
			l.log = self.log
			l.setFiles(self.getFiles(), *o.files)
			return l
		elif 'write' in dir(o) :
			l = self.reset(self.getLogTime())
			l.file = o + self.file if commut else self.file + o
			return l
		else :
			return None

	def __radd__(self, o) :
		return self.__add__(o, commut=True) #Use the add operator. It's commutative!!


	def __bool__(self) :
		"""
		False if log is empty.
		"""
		return bool(self.log)

	def __getitem__(self, i) :
		"""
		Supports slicing and indexing, from recent (0) to oldest (end).
		"""
		if isinstance(i, slice) :
			l = self.reset(self.getLogTime())
			for ind, itm in enumerate(self.log) :
				if ind in list(range(i.start if i.start else 0, i.stop, i.step if i.step else 1)): l.log.append(itm)
			return list(l)
		else :
			l = self.log[::-1][i]
			return self.compItem(l['state'], l['time'], l['text'], noCol = not self._useCol)

	def __len__(self) :
		"""
		Amount of items in the log.
		"""
		return len(self.log)

	def __iter__(self) :
		"""
		Iterator never colors output.
		"""
		return iter(self.compItem(l['state'], l['time'], l['text'], noCol = True) for l in self.log)

class LogFile() :
	"""
	Similar to a normal file, except it splits into several files. On the frontend, however, it acts as if it were a single file.
	
	*Writes to 'path'.log.
	*When maxLen is exceeded, lines are pushed into 'path'.0.log, then 'path'.1.log, etc. .
	"""
	def __init__(self, path, maxLen=1000, trunc=False) : #Make maxLen 1000 later.
		"""
		Constructor accepts a path (extension will be rewritten to '.log'), a maximum length, and will optionally truncate
		any previous logfiles.
		"""
		self.path = os.path.splitext(path)[0] + '.log'
		self.bPath = os.path.splitext(self.path)[0]
		
		self.maxLen = maxLen
		self.name = '<{0}.log, {0}.0...n.log>'.format(self.bPath)
		
		self.lines = 0
		self.fileNum = 0
		
		#If the logfile already exists, it's read + rewritten using the current maxLen.
		if os.path.exists(self.path) :
			if trunc: self.truncate(); return
			
			inLines = open(self.path, 'r').readlines()[::-1]
			os.remove(os.path.abspath(self.path)) #Remove the old path.log.
			
			i = 0
			while os.path.exists('{0}.{1}.log'.format(self.bPath, i)) :
				inLines += open('{0}.{1}.log'.format(self.bPath, i), 'r').readlines()[::-1]
				os.remove(os.path.abspath('{0}.{1}.log'.format(self.bPath, i)))
				i += 1
							
			self.write(''.join(reversed(inLines)))
			
	
	def write(self, *inStr) :
		apnd = list(filter(bool, ''.join(inStr).strip().split('\n')))
		
		if not apnd: return #Nothing to append = don't even try!
		if not os.path.exists(self.path): open(self.path, 'w').close() #Make sure path.log exists.
				
		#Empty apnd line by line.
		while len(apnd) > 0 :
			toWrite = self.maxLen * (self.fileNum + 1) - self.lines #Lines needed to fill up path.log
			if toWrite == 0 : #Time to make new files.		
						
				#Rename upwards. path.n.log -> path.(n+1).log, etc. . path.log becomes path.0.log.
				for i in reversed(range(self.fileNum)) :
					os.rename('{0}.{1}.log'.format(self.bPath, i), '{0}.{1}.log'.format(self.bPath, i+1))
				os.rename('{0}.log'.format(self.bPath), '{0}.0.log'.format(self.bPath))
				
				#Make new path.log.
				open(self.path, 'w').close() #Just create the file.
				
				#Number of files just increased.
				self.fileNum += 1
			else : #Fill up path.log.
				print(apnd.pop(0), file=open(self.path, 'a'))
				
				#Number of written lines just increasd.
				self.lines += 1
		
	def read(self) :
		collec = []
		
		for i in reversed(range(self.fileNum)) :
			collec += open('{0}.{1}.log'.format(self.bPath, i), 'r').readlines()
			
		collec += open(self.path, 'r').readlines()
		
		return ''.join(collec)
		
	def truncate(self) :
		"""
		Deletes all associated files + resets the instance.
		"""
		i = 0
		
		os.remove(os.path.abspath(self.path)) #Remove the old path.log.
		while os.path.exists('{0}.{1}.log'.format(self.bPath, i)) : #Remove all log files.
			os.remove(os.path.abspath('{0}.{1}.log'.format(self.bPath, i)))
			i += 1
			
		self.lines = 0
		self.fileNum = 0
		
	def readlines(self) :
		return self.read().split('\n')
		
	def isatty(self) :
		"""
		Always returns false, as a LogFile is never associated with a tty.
		"""
		return False
		
	def __iter__(self) :
		return (line for line in self.readlines())
		
	def __repr__(self) :
		return 'LogFile({0}, maxLen={1})'.format(self.path, self.maxLen)

def coolTest() :
	l = Log(Files(LogFile('first', 10, True), LogFile('second', 20, True)), LogFile('third', 30, True), sys.stdout)
	l(0, 'info', 'Big Failure Oh NO!')
	l(0, 'error', 'Big Failure Oh NO!')
	l(0, 'crit', 'Big Failure Oh NO!')
	l(0, 'warn', 'Big Failure Oh NO!')
	l(0, 'debug', 'Big Failure Oh NO!')
	l(0, 'run', 'Big Failure Oh NO!')
	
	print('We got ourselves a log file here kids.')
	
	for i in range(50) :
		l(0, 'run', 'This is the', i, 'run today!')
	
	print(l.getLogTime())

def logFileTest() :
	l = LogFile('hi.log', maxLen = 3, trunc=True)
	
	print('\n', repr(l), sep='')
	print('hi', 'world', file=l, sep='\n')
	
	print('\n', repr(l), sep='')
	print('you', 'are', 'cool', 'friend', 'hi', file=l, sep='\n')
	print('hello\nmotherfucker\nits\narnold\nyour\nold\nfriend\nrunbaby!!\nlittlebitch :)', file=l)
	print('\n', repr(l), sep='')
	print('Reading Log Files:', repr(l.read()))
	print(l.name, '\n\n\n')
	
	print(l.read().split('\n'))
	print(len([x for x in l.read().split('\n') if x]))
	
	l = LogFile('hi.log', 10)
	print(l.read().split('\n'))
	print(len([x for x in l.read().split('\n') if x]))
		
	l = Log(LogFile('hi', 100, False))
	print(repr(l))
	for x in range(10) :
		l(0, x)
	#~ l.setCol(False)
	l(0, 'info', 'Big Failure Oh NO!')
	l(0, 'error', 'Big Failure Oh NO!')
	l(0, 'crit', 'Big Failure Oh NO!')
	l(0, 'warn', 'Big Failure Oh NO!')
	l(0, 'debug', 'Big Failure Oh NO!')
	l(0, 'run', 'Big Failure Oh NO!')
	l = LogFile('hi', 500, False)
	print('hihi', 'you', 'can\'t', 'beat', 'the', 'trunc', file=l, sep='\n')

def logTest() :
		l = Log(open('hi.txt', 'w'))
		#~ l.setCol(False)
		print(repr(l))
		print('1', file=l)
		l(1, '2')
		a = l.reset()

		#~ l.setCol(True)

		l.addFiles(sys.stderr)
		print('\n', repr(l), sep='')

		print('\n', repr(a), sep='')
		a(2, '3')
		a.write('4')
		a.addFiles(sys.stdout)

		print('\n a + l ', repr(a + l), sep='')

		print(a + l)

		print('\n', repr(a + sys.stderr), sep='')
		print('\n', repr(sys.stderr + a), sep='')
		print('\n', (l + a), sep='')
		print('\n', (l + a)[0:3], sep='')

		for item in (l + a) :
			print(item)

		print("\nLength of l + a: ", len(l + a))
		print("\nl + a: ", repr(Log() + Files(sys.stdout)))
		print('\n', l.read(verb=0), sep='')

if __name__ == "__main__" :
	#~ unitTest()
	#~ logFileTest()
	coolTest()
