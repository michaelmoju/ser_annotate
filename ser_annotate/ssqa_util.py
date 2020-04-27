#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
import re
import xml.sax.saxutils
from collections import Counter

from .std import *

from . import Const

_log = logging.getLogger(__name__)

# Due to backward compatibility, '//' is used to separate Word-POS pair.
# Since a word may consists of '//' (such as http://www.cwb.gov.tw), the following regular expression is used to split a Word-POS pair.
_rgx = re.compile(r'^(.*)//([^/]*)$')

# SSQA text should not consist of the following ASCII chars
_rgx_chk_unescaped = re.compile(r'([\t\r\n#$&\'*<?@^_`{|}])')
_rgx_chk_escaped = re.compile(r'([\t\r\n#$\'*<>?@^_`{|}])')
# SSQA text should not consist of the following strings
_rgx_chk_str = re.compile(r'(\|\||&&)')
_rgx_ckip_rel_headline = re.compile(r'(.*)\[(\d+)\]\s+(.*)#')


# I will use the following strings as separators for SSQA system
#	'{', '}', '|', '||', '|||', ...
# Although the texts of SSQA corpus do not consist of SPACE character (i.e., ' '),
# I will not use ' ' as a separator because ordinary English texts consist of a lot of SPACE characters.

def check_unescaped_text(txt):
	m = _rgx_chk_unescaped.search(txt)
	if m:
		eprint('\n"{}"\nconsists of [{}]'.format(txt, m.group(0)))
		raise ValueError
	m = _rgx_chk_str.search(txt)
	if m:
		eprint('\n"{}"\nconsists of [{}]'.format(txt, m.group(0)))
		raise ValueError


def check_escaped_text(txt):
	m = _rgx_chk_escaped.search(txt)
	if m:
		eprint('\n"{}"\nconsists of [{}]'.format(txt, m.group(0)))
		raise ValueError
	m = _rgx_chk_str.search(txt)
	if m:
		eprint('\n"{}"\nconsists of [{}]'.format(txt, m.group(0)))
		raise ValueError


def xml_escape(txt):
	# xml.sax.saxutils.escape(data, entities={})
	# Escape '&', '<', and '>' in a string of data.
	return xml.sax.saxutils.escape(txt)


def xml_unescape(txt):
	# xml.sax.saxutils.unescape(data, entities={})
	# Unescape '&amp;', '&lt;', and '&gt;' in a string of data.
	return xml.sax.saxutils.unescape(txt)


# a block is a line not leading with '\t' and its optional following lines leading with '\t' (or empty lines)
def read_block(f, keep_empty_line=False):
	myOut = []
	for myLine in (x.rstrip() for x in f):
		# _log.debug('>>{}<<'.format(myLine))
		if not myLine:
			if not keep_empty_line: continue
			if myOut: myOut.append(myLine)
		else:
			if myLine[0] != '\t':
				if myOut: yield myOut
				myOut = []
			myOut.append(myLine)
	if myOut: yield myOut


# a qt-blocks is a list of blocks whose first element is a question block and the other elements are evidence blocks
def read_qt_blocks(f):
	myOut = []
	for myBlock in read_block(f):
		if myBlock[0][0] == 'Q':  # question block's first character
			if myOut: yield myOut
			myOut = []
		else:
			insist(myBlock[0][0] in 'TN')  # evidence block's first character
		myOut.append(myBlock)
	if myOut: yield myOut


def get_word_counter(snts, keep_stop_word):
	myCounter = Counter()
	for mySnt in snts:
		if keep_stop_word:
			myCounter.update(x.split(Const.sep_bar1)[0] for x in mySnt.strip().split(Const.sep_bar2))
		else:
			myCounter.update(x.split(Const.sep_bar1)[0] for x in mySnt.strip().split(Const.sep_bar2) if not x.endswith('-SW'))
	return myCounter


def get_sequence(snts, keep_stop_word):
	myOut = []
	for mySnt in snts:
		if keep_stop_word:
			myOut.extend(x.split(Const.sep_bar1) for x in mySnt.strip().split(Const.sep_bar2))
		else:
			myOut.extend(x.split(Const.sep_bar1) for x in mySnt.strip().split(Const.sep_bar2) if not x.endswith('-SW'))
	return myOut


def get_word_sequence(snts, keep_stop_word):
	myOut = []
	for mySnt in snts:
		if keep_stop_word:
			myOut.extend(x.split(Const.sep_bar1)[0] for x in mySnt.strip().split(Const.sep_bar2))
		else:
			myOut.extend(x.split(Const.sep_bar1)[0] for x in mySnt.strip().split(Const.sep_bar2) if not x.endswith('-SW'))
	return myOut


def get_pos_sequence(snts, keep_stop_word):
	myOut = []
	for mySnt in snts:
		if keep_stop_word:
			myOut.extend(x.split(Const.sep_bar1)[1] for x in mySnt.strip().split(Const.sep_bar2))
		else:
			myOut.extend(x.split(Const.sep_bar1)[1] for x in mySnt.strip().split(Const.sep_bar2) if not x.endswith('-SW'))
	return myOut


# a block in the output file of pst2rel
def ckip_read_pst2rel_block(f):
	myOut = []
	for myLine in (x.rstrip() for x in f):
		if myLine:
			myOut.append(myLine)
		else:
			if myOut:
				yield myOut
				myOut = []
	if myOut: yield myOut

def ckip_read_rel_data(f):
	for (myHeadline, *myRels) in ckip_read_pst2rel_block(f):
		myKey, mySntIdx, myPstExpr = _rgx_ckip_rel_headline.match(myHeadline).groups()
		yield myKey, int(mySntIdx), myPstExpr, tuple(myRels)

# transform an output line in the output file of pst2rel
def ckip_rel2dep(out_line):
	myCols = out_line.split('\t')
	insist(myCols[-1] == '1')
	myCols.pop(-1)
	insist(len(myCols) == 6)
	myLhsRole, myLhsWrd, myLhsPos, myRhsRole, myRhsWrd, myRhsPos = myCols
	myHeadNum = 1
	if myLhsRole.startswith('Head['):
		myGov, myDep, myRel = myLhsWrd, myRhsWrd, myRhsRole
		if myRhsRole.startswith('Head['):
			myHeadNum = 2
	else:
		myGov, myDep, myRel = myRhsWrd, myLhsWrd, myLhsRole
		if not myRhsRole.startswith('Head['):
			myHeadNum = 0
	return (myGov, myRel, myDep), myHeadNum, myCols

# Tokenize a string.
# Tokens yielded are of the form (type, string)
# Possible values for 'type' are '(', ')' and 'S'
def ckip_pst_expr2terms(s):
	myTokens = re.compile('\s+|[|()]|[^\s|()]+')
	for m in myTokens.finditer(s):
		s = m.group(0).strip()
		if not s:
			continue
		if s[0] in '|()':
			yield (s, s)
		else:
			yield ('S', s)


# Parse once we're inside an opening bracket.
def ckip_pst_terms2parse_inner(terms, vlst):
	myType, mySym = terms.pop(0)
	insist(myType == '(')
	myKids = []
	while myType != ')':
		myKids.append(ckip_pst_terms2parse(terms, vlst))
		myType, mySym = terms.pop(0)
		insist(myType in ['|', ')'])
	return myKids


def ckip_pst_terms2parse(terms, vlst=None):
	# S(theme:NP(Head:Nab:書套)|Head:V_2:有|range:DM:幾個)
	if vlst is None:
		vlst = [1]  # next terminal index
	myType, mySym = terms.pop(0)
	insist(myType == 'S')

	myNextType = terms[0][0]
	insist(myNextType != 'S')

	myBegTid = vlst[0]

	myKids = []
	if myNextType == '(':
		# nonterminal
		myKids = ckip_pst_terms2parse_inner(terms, vlst)
	else:
		# terminal
		vlst[0] += 1

	myEndTidx = vlst[0]
	return (mySym, myKids, myBegTid, myEndTidx)


def ckip_pst2bkf(tree, depth=0):
	myIndent = '\t' * depth
	mySym, myKids, myBegTid, myEndTid = tree
	if len(myKids) == 0:  # a terminal node
		m = re.search(r'^([^:]+):([^:]+):(.+)$', mySym)
		insist(m)
		myRole, myPos, myWrd = m.groups()
		return '%s(%s//%s)' % (myIndent, myWrd, myPos);
	else:  # a nonterminal node
		myStr = '%s(%s' % (myIndent, mySym)
		for myKid in myKids:
			myStr += '\n'
			myStr += ckip_pst2bkf(myKid, depth + 1)
		return myStr + ')'


def ckip_pst2tkns(tree):
	mySym, myKids, myBegTid, myEndTid = tree
	myOut = []
	if len(myKids) == 0:
		# a terminal node
		m = re.search(r'^([^:]+):([^:]+):(.+)$', mySym)
		insist(m)
		myRole = m.group(1)
		myPos = m.group(2)
		myWrd = m.group(3)
		myOut.append((myWrd, myPos))
	else:
		for myKid in myKids:
			myOut += ckip_pst2tkns(myKid)
	return myOut

