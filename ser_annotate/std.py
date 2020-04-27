#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
import operator
import os, sys
import pickle
import random
import subprocess
import shutil
import gzip
import bisect
from collections import Counter
from decimal import Decimal
import json
import xml.sax.saxutils

import logging
from logging.handlers import QueueHandler

import itertools

_log = logging.getLogger(__name__)
_DEBUG = False


# Bunch pattern (see page 32 in "Python Algorithms: Mastering Basic Algorithms in the Python Language (2e) [Magnus Lie Hetland] (2014)")
class Bunch(dict):
	def __init__(self, *args, **kwds):
		super().__init__(*args, **kwds)
		self.__dict__ = self


def rand_init():
	# initialize random number generator to make procedures repeatable
	# random.seed(a=None, version=2)
	#    Initialize the random number generator.
	#    If a is omitted or None, the current system time is used. If randomness sources are provided by the operating system, they are used instead of the system time (see the os.urandom() function for details on availability).
	#    If a is an int, it is used directly.
	#    With version 2 (the default), a str, bytes, or bytearray object gets converted to an int and all of its bits are used. With version 1, the hash() of a is used instead.
	#    Changed in version 3.2: Moved to the version 2 scheme which uses all of the bits in a string seed.
	random.seed(1, 2)


# open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None)
# When reading input from the stream, if newline is None, universal newlines mode is enabled. Lines in the input can end in '\n', '\r', or '\r\n', and these are translated into '\n' before being returned to the caller.
# When writing output to the stream, if newline is None, any '\n' characters written are translated to the system default line separator, os.linesep. If newline is '' or '\n', no translation takes place.
def open_r(filename):
	if filename.endswith('.gz'):
		return gzip.open(filename, 'rt', encoding='utf-8')
	return open(filename, 'r', -1, 'utf-8')


def open_rb(filename):
	if filename.endswith('.gz'):
		return gzip.open(filename, 'rb')
	return open(filename, 'rb')


def skip_w(filename, force):
	if not force and os.path.exists(filename):
		eprint('>>Skip', filename)
		return True
	return False


class _Devnull:
	def write(self, *_): pass

	def flush(self): pass

	def __enter__(self): return self

	def __exit__(self, exc_type, exc_val, exc_tb): pass


def open_w(filename, force=True):
	if filename == os.devnull:
		return _Devnull()
	if not force:
		insist(not os.path.exists(filename), '{} exists!'.format(filename))
	myDir = os.path.dirname(filename)
	if myDir and not os.path.exists(myDir):
		os.makedirs(myDir)
	if filename.endswith('.gz'):
		return gzip.open(filename, 'wt', encoding='utf-8', newline='\n')
	return open(filename, 'w', -1, 'utf-8', None, '\n')


def open_wb(filename, force=True):
	if filename == os.devnull:
		return _Devnull()
	if not force:
		insist(not os.path.exists(filename), '{} exists!'.format(filename))
	myDir = os.path.dirname(filename)
	if myDir and not os.path.exists(myDir):
		os.makedirs(myDir)
	if filename.endswith('.gz'):
		return gzip.open(filename, 'wb')
	return open(filename, 'wb')


def open_a(filename):
	if filename == os.devnull:
		return _Devnull()
	myDir = os.path.dirname(filename)
	if myDir and not os.path.exists(myDir):
		os.makedirs(myDir)
	if filename.endswith('.gz'):
		return gzip.open(filename, 'at', encoding='utf-8', newline='\n')
	return open(filename, 'a', -1, 'utf-8', None, '\n')


def insist(expr, mesg=''):
	if not expr:
		if mesg: eprint(mesg)
		assert False


def pickle_load(ifh):
	while True:
		try:
			yield pickle.load(ifh)
		except EOFError:
			break


def prompt(*args, **kwargs):
	print(*args, flush=True, **kwargs)


def fnln():
	import inspect
	callerFrame = inspect.stack()[1]  # 0 represents this line
	myInfo = inspect.getframeinfo(callerFrame[0])
	myFilename = os.path.basename(myInfo.filename)
	return '{}({})'.format(myFilename, myInfo.lineno)


def lprint(*args, **kwargs):
	import inspect
	callerFrame = inspect.stack()[1]  # 0 represents this line
	myInfo = inspect.getframeinfo(callerFrame[0])
	myFilename = os.path.basename(myInfo.filename)
	print('{}({}):'.format(myFilename, myInfo.lineno), *args, flush=True, file=sys.stderr, **kwargs)


def eprint(*args, **kwargs):
	print(*args, flush=True, file=sys.stderr, **kwargs)


def call(cmd, quiet=False):
	if (not quiet): prompt(cmd)
	logging.log(1, cmd)
	subprocess.call(cmd, shell=True)
	logging.log(1, '')


def new_dir(dir_path, clear=True):
	if os.path.exists(dir_path) and clear:
		prompt('Remove ' + dir_path)
		shutil.rmtree(dir_path)
	if not os.path.exists(dir_path):
		prompt('Create ' + dir_path)
		os.makedirs(dir_path)


def log_w(filename, force=True):
	if not force:
		insist(not os.path.exists(filename), '{} exists!'.format(filename))
	myDir = os.path.dirname(filename)
	if myDir and not os.path.exists(myDir):
		os.makedirs(myDir)
	return logging.FileHandler(filename, 'w', 'utf-8')


def log(logger, msg, *args, **kwargs):
	logger.log(100, msg, *args, **kwargs)


def str2llv(s):
	# Level		Numeric value
	# CRITICAL  50
	# ERROR		40
	# WARNING   30
	# INFO		20
	# DEBUG		10
	# NOTSET	 0
	if s == 'FATAL': return logging.FATAL
	if s == 'ERROR': return logging.ERROR
	if s == 'WARN': return logging.WARN
	if s == 'INFO': return logging.INFO
	if s == 'DEBUG': return logging.DEBUG
	if s == 'NOTSET': return logging.NOTSET
	try:
		return int(s)
	except ValueError:
		insist(False, 'Not able to convert "{}" to an integer!'.format(s))


def pct(n, d):
	return '{:.2%} (={}/{})'.format(float(n) / d, n, d)


def print_counter(cnt, key_idx=0, reverse=False, topn=0):
	myDeno = sum(cnt.values())
	if reverse:
		for i, (k, v) in enumerate(reversed(sorted(cnt.items(), key=operator.itemgetter(key_idx)))):
			if i > topn > 0: break
			print('{}\t{:d}\t{}'.format(k, v, pct(v, myDeno)))
	else:
		for i, (k, v) in enumerate(sorted(cnt.items(), key=operator.itemgetter(key_idx))):
			if i > topn > 0: break
			print('{}\t{:d}\t{}'.format(k, v, pct(v, myDeno)))


def drange(start, stop, step, le=False, qn=None, exp2=False):
	x, y, z = Decimal(str(start)), Decimal(str(stop)), Decimal(str(step))
	# x, y, z = start, stop, step
	while x <= y:
		if x == y and not le: break
		myOut = 2 ** x if exp2 else x
		if qn:
			yield str(Decimal(myOut).quantize(Decimal(qn)).normalize())
		else:
			yield float(x)
		x = x + z


def dq_f(f, qn='0.0001'):
	return Decimal(f).quantize(Decimal(qn))


def dqn_f(f, qn='0.0001'):
	return Decimal(f).quantize(Decimal(qn)).normalize()


def str_f(f, qn='0.0001'):
	return str(dqn_f(f, qn))


def mpw_init(log_queue, log_level):  # mwp(Multi-Processing-Worker
	# all records from worker processes go to {myHandler} and then into {log_queue}
	myHandler = QueueHandler(log_queue)
	logger = logging.getLogger()
	logger.setLevel(log_level)
	logger.addHandler(myHandler)


def jseq_load(ifh):
	for myLine in ifh:
		yield json.loads(myLine)


def jseq_dump(seq, ofh):
	for x in seq:
		# lprint(x)
		json.dump(x, ofh)
		ofh.write('\n')


# i       bisect_left     bisect_right
# 0       (-INF,0.1]      [-INF,0.1)
# 1       (0.1,0.2]       [0.1,0.2)
# 2       (0.2,0.3]       [0.2,0.3)
# 3       (0.3,0.4]       [0.3,0.4)
# 4       (0.4,0.5]       [0.4,0.5)
# 5       (0.5,+INF]      [0.5,+INF)
# v=0     0               0
# v=0.1   0               1
# v=0.2   1               2
# v=0.3   2               3
# v=0.4   3               4
# v=0.5   4               5
# v=0.6   5               5
class Quantizer:
	def __init__(self, bps, range_type):
		self.__bps = [Decimal(str(x)) for x in bps]  # breakpoints
		if range_type == '[)':
			self.__bisect = bisect.bisect_right
		elif range_type == '(]':
			self.__bisect = bisect.bisect_left
		else:
			raise ValueError('range_type={}'.format(range_type))
		self.__tag = []
		# eprint('i\tbisect_left\tbisect_right')
		for i in range(len(self.__bps) + 1):
			myPrv = str(self.__bps[i - 1]) if i - 1 >= 0 else '-INF'
			myVal = str(self.__bps[i]) if i < len(self.__bps) else '+INF'
			# eprint('{:d}\t({},{}]\t[{},{})'.format(i, myPrv, myVal, myPrv, myVal))
			if range_type == '[)':
				myTag = '[{},{})'.format(myPrv, myVal) if i > 0 else '({},{})'.format(myPrv, myVal)
			elif range_type == '(]':
				myTag = '({},{}]'.format(myPrv, myVal) if i < len(self.__bps) else '({},{})'.format(myPrv, myVal)
			else:
				raise ValueError('range_type={}'.format(range_type))
			self.__tag.append(myTag)

	# eprint(i,myTag)

	def bisect(self, val):
		# eprint('val\tleft(val)\tright(val)')
		i = bisect.bisect_left(self.__bps, Decimal(str(val)))
		j = bisect.bisect_right(self.__bps, Decimal(str(val)))
		eprint('v={}\t{}\t\t{}'.format(str(val), str(i), str(j)))

	def tag(self, val):
		# bisect.bisect_left(a, x, lo=0, hi=len(a))
		#	The returned insertion point i partitions the array a into two halves so that
		#		all(val < x for val in a[lo:i]) for the left side and
		#		all(val >= x for val in a[i:hi]) for the right side.
		#
		# LYC: smallest i such that x >= a[i]

		# bisect.bisect_right(a, x, lo=0, hi=len(a))
		# bisect.bisect(a, x, lo=0, hi=len(a))
		#	The returned insertion point i partitions the array a into two halves so that
		#		all(val <= x for val in a[lo:i]) for the left side and
		#		all(val > x for val in a[i:hi]) for the right side.
		#
		# LYC: smallest i such that x < a[i]
		i = self.__bisect(self.__bps, Decimal(str(val)))
		return self.__tag[i]

	def idx(self, val):
		# bisect.bisect_left(a, x, lo=0, hi=len(a))
		#	The returned insertion point i partitions the array a into two halves so that
		#		all(val < x for val in a[lo:i]) for the left side and
		#		all(val >= x for val in a[i:hi]) for the right side.
		#
		# LYC: smallest i such that x >= a[i]

		# bisect.bisect_right(a, x, lo=0, hi=len(a))
		# bisect.bisect(a, x, lo=0, hi=len(a))
		#	The returned insertion point i partitions the array a into two halves so that
		#		all(val <= x for val in a[lo:i]) for the left side and
		#		all(val > x for val in a[i:hi]) for the right side.
		#
		# LYC: smallest i such that x < a[i]
		return self.__bisect(self.__bps, Decimal(str(val)))


def _test__Quantizer():
	# myBps = list(drange(0.1, 0.5, 0.1, le=True))
	myBps = [0.2, 0.4, 0.6]
	# myQuantizer = Quantizer(myBps,'(]')
	myQuantizer = Quantizer(myBps, '[)')
	myBps = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
	for i in myBps:
		#		myQuantizer.bisect(i)
		eprint('myQuantizer.tag({})={}'.format(i, myQuantizer.tag(i)))
		eprint('myQuantizer.idx({})={}'.format(i, myQuantizer.idx(i)))


def _test__Quantizer2():
	# myBps = list(drange(0.1, 0.5, 0.1, le=True))
	myQuantizer = Quantizer([float(i) / 10 for i in range(10)], '[)')
	for i in [float(i) / 10 for i in range(11)]:
		eprint('myQuantizer.tag({})={}'.format(i, myQuantizer.tag(i)))
		eprint('myQuantizer.idx({})={}'.format(i, myQuantizer.idx(i)))


def _test__itertools__chain__from_iterable():
	import itertools
	a = [[1, 2], [3], [4, [5, 6]]]
	a = [[(1, 2), (3, 4)], [(5, 6)]]
	eprint('a=', a)
	for i in itertools.chain.from_iterable(a):
		eprint('i=', i)


# Q: Should I scale training and testing data in a similar way?
# Yes, you can do the following:
# > svm-scale -s scaling_parameters train_data > scaled_train_data
# > svm-scale -r scaling_parameters test_data > scaled_test_data
#
# Q: Does it make a big difference if I scale each attribute to [0,1] instead of [-1,1]?
# For the linear scaling method, if the RBF kernel is used and parameter selection is conducted, there is no difference.
# ...
# Hence, using (C,g) on the [0,1]-scaled data is the same as (C,g/2) on the [-1,1]-scaled data.
# Though the performance is the same, the computational time may be different. For data with many zero entries, [0,1]-scaling keeps the sparsity of input data and hence may save the time.
def svm_save_scaling_parameters(fn, feats, out_range):
	myRangeVec = None
	if out_range:
		insist(len(feats) > 0)
		# value = y_lower + (y_upper - y_lower) * (value - y_min) / (y_max - y_min);
		for myFeatDict in feats:
			if myRangeVec is None:
				myRangeVec = [out_range]
				for k, v in sorted(myFeatDict.items(), key=operator.itemgetter(0)):
					insist(len(myRangeVec) == k)
					myRangeVec.append([v, v])
			else:
				insist(len(myFeatDict) + 1 == len(myRangeVec))
				for k, v in sorted(myFeatDict.items(), key=operator.itemgetter(0)):
					myRange = myRangeVec[k]
					if myRange[0] > v: myRange[0] = v
					if myRange[1] < v: myRange[1] = v
	myOut = myRangeVec
	if fn is not None:
		with open_w(fn) as ofh:
			json.dump(myOut, ofh, indent='\t', sort_keys=False, ensure_ascii=True)
	return myOut


def svm_load_scaling_parameters(fn):
	with open_r(fn) as ifh:
		return json.load(ifh)


def svm_scale(sp, xs):
	if sp is not None:
		mySclPara = [[x[0], x[1] - x[0]] for x in sp]
		myOutMin, myOutLen = mySclPara[0]
		insist(myOutLen > 0)
		for myFeatDict in xs:
			insist(len(myFeatDict) + 1 == len(sp))
			for k in myFeatDict.keys():
				# value = y_lower + (y_upper - y_lower) * (value - y_min) / (y_max - y_min);
				myInpMin, myInpLen = mySclPara[k]
				if myInpLen != 0:
					insist(myInpLen > 0)
					myFeatDict[k] = myOutMin + myOutLen * (myFeatDict[k] - myInpMin) / myInpLen


# https://www.python.org/dev/peps/pep-0485/#proposed-implementation
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
	if a == b:  # short-circuit exact equality
		return True
	return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


# a is less than b
def islt(a, b, rel_tol=1e-09, abs_tol=0.0):
	if isclose(a, b, rel_tol, abs_tol): return False
	return a < b


# a is greater than b
def isgt(a, b, rel_tol=1e-09, abs_tol=0.0):
	if isclose(a, b, rel_tol, abs_tol): return True
	return a > b


def _f_measure(p, r):
	# F-measure: F = 2 / ( 1 / P + 1 / R) = 2 * P * R / ( P + R )
	myNume = 2 * p * r
	if myNume == 0: return 0
	return myNume / (p + r)


def counters_p_r_f(ref_cnt, hyp_cnt):
	assert type(ref_cnt) == type(hyp_cnt) == Counter
	if len(ref_cnt) == 0 or len(hyp_cnt) == 0:
		p, r, f = 0, 0, 0
	else:
		myCommon = (ref_cnt & hyp_cnt)
		p = float(sum(myCommon.values())) / float(sum(hyp_cnt.values()))
		r = float(sum(myCommon.values())) / float(sum(ref_cnt.values()))
		f = _f_measure(p, r)
		if __debug__:
			if _DEBUG:
				_log.debug('ref_cnt={}'.format(str(ref_cnt)))
				_log.debug('hyp_cnt={}'.format(str(hyp_cnt)))
				_log.debug('{} {} {}'.format(p, r, f))
	return p, r, f


def xml_escape(txt):
	# xml.sax.saxutils.escape(data, entities={})
	# Escape '&', '<', and '>' in a string of data.
	return xml.sax.saxutils.escape(txt)


def xml_unescape(txt):
	# xml.sax.saxutils.unescape(data, entities={})
	# Unescape '&amp;', '&lt;', and '&gt;' in a string of data.
	return xml.sax.saxutils.unescape(txt)


def zzip(*i):
	assert len(i) > 1
	for j in itertools.zip_longest(*i):
		for k in j: assert k is not None
		yield j


_LOG_TENSORS = True


def _log_tsr_imp(ndas, names, caller, lvl):
	def _indent(text, indent='\t'):
		return ''.join('{}{}\n'.format(indent, x) for x in text.split('\n'))

	_log.log(lvl, '>>%s', caller)
	for n, a in zzip(names, ndas):
		_log.log(lvl, '\t%s=%s\n%s', n, a.shape, _indent(str(a), '\t\t').rstrip())


class Logger:
	def __init__(self, name):
		self.__logger = logging.getLogger(name)
		self.__pyf_arg = Bunch()

	# __getattribute__ will be called for every access, and
	# __getattr__ will be called for the times that __getattribute__ raised an AttributeError
	def __getattr__(self, item):
		return self.__logger.__getattribute__(item)

	def to_debug(self):
		return self.__logger.isEnabledFor(logging.DEBUG)

	def to_info(self):
		return self.__logger.isEnabledFor(logging.INFO)

	def log_platform_info(self):
		import platform as pf
		self.__logger.log(100, '{}, {}, Python-{}'.format(pf.node(), pf.platform(), pf.python_version()))


