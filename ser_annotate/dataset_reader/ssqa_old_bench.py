import difflib
import re

from ..std import *

_log = logging.getLogger(__name__)
_PUNCT_SET = frozenset(["，", ",", "、", "；", "。", "：", "！", "!", "？", "?"])

def string_split(str):
    myOut = []
    mySeg = ''
    for iChar in str:
        mySeg += iChar
        if iChar in _PUNCT_SET:
            myOut.append(mySeg)
            mySeg = ''
    if mySeg:
        myOut.append(mySeg)
    return myOut

def get_parag_idx(myP):
    outIdx = []
    myKey, myTxt = myP
    mySegTxt = string_split(myTxt)
    outIdx.extend(list(range(0, len(mySegTxt))))
    return outIdx

def get_idx(iPs, iBen):
    outIdx = []
    benKey, benTxt = iBen
    benKeyNum = int(re.search('Pub.-G\d[ab]-\d{4}-(\d{3})', benKey).group(1))
    # if re.match('.*\|{3,}.*',benTxt):
    # lprint("match|||")
    myBenSegs = string_split(re.sub('\|{3,}', '', benTxt))
    iPs[benKeyNum - 1]
    myParSegs = string_split(iPs[benKeyNum - 1][1])
    mySeqMat = difflib.SequenceMatcher(None, myBenSegs, myParSegs)
    for tag, i1, i2, j1, j2 in mySeqMat.get_opcodes():
        _log.debug('{:7}   a[{}:{}] --> b[{}:{}] {!r:>8} --> {!r}'.format(
            tag, i1, i2, j1, j2, myBenSegs[i1:i2], myParSegs[j1:j2]))
    for tag, i1, i2, j1, j2 in mySeqMat.get_opcodes():
        if tag == 'equal':
            outIdx.extend(list(range(j1, j2)))
        else:
            if tag != 'insert':
                raise ValueError('{}\n{}\n'.format(myBenSegs, myParSegs))
    # if re.match('.*\|{3,}.*', benTxt):
    # lprint(outIdx)
    return outIdx

def read_dats(f):
    myPs, myQs = [], []
    myQ = []
    for myLine in (x.rstrip() for x in f):
        # _log.debug('>>{}<<'.format(myLine))
        if not myLine: continue  # pass the empty line
        if myLine[0] == 'P':  # read lesson text
            if myQs:
                yield myPs, myQs
                myPs, myQs = [], []
            myKey, myTxt = myLine.split('\t')
            myPs.append([myKey, myTxt])
        elif myLine[0] == '0':
            assert not myQ
            myQ = myLine.split('\t')
            assert len(myQ) == 2
        elif myLine[0] == 'b':
            assert len(myQ) == 2
            myKey, *myToks = myLine.split('\t')
            if len(myToks) == 1 and myToks[0] == 'NONE':
                myQs.append(myQ)
                myQ = []
            else:
                for iTok in myToks:
                    myKey, myTxt = iTok.split()
                    assert myKey.startswith('Pub')
                    myQ.append([myKey, myTxt])
                myQs.append(myQ)
                myQ = []
    yield myPs, myQs
    
def read_old_benchmark(fp):
    """
    read old SSQA supporting evidence benchmark.
    Latest version: SSQA_benchmark_v3.2_0312
    """
    with open(fp) as f:
        totQsNum = 0
        myLessons = {}
        for i, (myPs, myQs) in enumerate(read_dats(f), 1):
            myFid2Bens = {}
            myFid2Parg = []
            myBens = []
            myFid = None
            lesson_id = myPs[0][0][:-4]

            for iP in myPs:
                myKey, myTxt = iP
                myIdx = get_parag_idx(iP)
                myFid2Parg.append([myKey, myIdx])
            for iQ in myQs:
                myKey, myTxt, *myEvidParts = iQ
                for iEvidPart in myEvidParts:
                    a, b, c, d = iEvidPart[0].split('-')
                    if myFid is None:
                        myFid = '{}-{}-{}'.format(a, b, c)
                    assert myFid == '{}-{}-{}'.format(a, b, c)
                    iEvidPart.append(get_idx(myPs, iEvidPart))
                myBens.append([myKey, myTxt, myEvidParts])
            assert lesson_id not in myLessons
            myLessons[lesson_id] = [myFid2Parg, myBens]
            totQsNum += len(myQs)
        lprint("#Lesson:{}".format(len(myLessons)))
        lprint("#Question:{}".format(totQsNum))
        return myLessons


def inspect_old_bench(benches):
    num_p = 0
    num_s = 0
    num_q = 0
    num_l = len(benches)
    
    for lesson_id, lesson in benches.items():
        parags = lesson[0]
        Qs = lesson[1]
        
        num_q += len(Qs)
        num_p += len(parags)
        
        for pid, sents in parags:
            num_s += len(sents)
    
    print("#Lesson:{}".format(num_l))
    print("#Question:{}".format(num_q))
    print("Mean #paragraphs per lesson:{}".format(num_p / num_l))
    print("Mean #sentences per paragraph:{}".format(num_s / num_p))