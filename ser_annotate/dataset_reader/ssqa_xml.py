import re
import xml.etree.ElementTree as ET

from ..std import *
from ..Const import sep_bar1, sep_bar2
from .. import ssqa_util as Util
from .ssqa_old_bench import string_split

def _leaf2text(p):
    assert len(p) == 0
    myText = p.text.strip(' \t\r\n')
    insist(len(myText) > 0)
    insist(myText == p.text)
    insist(myText.find('\n') < 0)
    insist(myText.find('\r') < 0)
    insist(myText.find('\t') < 0)
    return myText

def _body2dat(p, dat, xpath=''):
    # for c in p: print(c.tag, c.attrib)
    myXpath = xpath
    if myXpath: myXpath += '/'
    myXpath += p.tag

    if len(p) == 0:
        # terminal
        dat.append((myXpath, _leaf2text(p)))
    else:
        # nonterminal
        for c in p: _body2dat(c, dat, myXpath)

def _qst2dat(qsts):
    q_dict = {'true-false':{}, 'multiple-choice':{}, 'multiple-select':{}}
    for q_i, q in enumerate(qsts):
        assert q.tag == 'QA'
        grade, qnum = re.search('IIS-MR-SOCIAL-GRADE(\d{2})-(\d{6})', q.attrib['ID']).groups()
        qid = grade + '-' + qnum
        qtype = q.attrib['Type']
        q_idx = q.attrib['idx']
            
        if qtype == 'true-false':
            q_text = q[0].text # question
            a = q[1].text # answer 對 or 錯
            assert qid not in q_dict['true-false'], "duplicate qid"
            q_dict['true-false'][qid] = (q_text, a)
            
        elif qtype == 'multiple-choice':
            q_text = q[0].text # question
            choices = [c.text for c in q[1]] # choice set
            a = int(q[2].attrib['idx'])-1 # answer idx
            assert qid not in q_dict['multiple-choice'], "duplicate qid"
            q_dict['multiple-choice'][qid] = (q_text, choices, a)
            
        elif qtype == 'multiple-select':
            q_text = q[0].text # question
            choices = [c.text for c in q[1]] # choice set
            a = [int(a.attrib['idx'])-1 for a in q[2]] # answer idx list
            assert qid not in q_dict['multiple-select'], "duplicate qid"
            q_dict['multiple-select'][qid] = (q_text, choices, a)
        
    return q_dict

def ssqa_xml2txt(fhs):
    outFh = 'Lesson.txt'

    myFid, myGrad = re.search('/(Pub.-G(\d)[ab]-\d{4})\.', fhs).groups()
    # lprint(myFid)
    tree = ET.parse(fhs)
    p = tree.getroot()
    for i in ['Machine-Reading-Corpus-File', 'Content', 'Unit']:
        assert p.tag == i
        if i != 'Unit':
            assert len(p) == 1
            p = p[0]
    assert len(p) == 2  # Body, QAset

    # read the lessons
    myBodyDat = []
    assert p[0].tag == 'Body'
    _body2dat(p[0], myBodyDat)
#     lprint(myBodyDat)

    myLessonTxt = ""
    s_start = 0
    
    out_parags = []
    for i, (iTag, iTxt) in enumerate(myBodyDat):
        
        Util.check_unescaped_text(iTxt)
        assert iTxt.find('&') < 0
        myTxt = Util.xml_escape(iTxt)
        Util.check_escaped_text(myTxt)
        if myTxt != iTxt:
            lprint('{}\n\t{}\n\t{}\n'.format(myFid, iTxt, myTxt))
        
        out_sents = []
        # sentence segmentation
        sents = string_split(iTxt)
        for sid, sTxt in enumerate(sents):
            if sid == len(sents)-1: #last sentencein paragraph
                s_end = s_start + len(sTxt)
                out_sents.append({'sid': sid, 'text': sTxt, 'start': s_start, 'end': s_end})
                myLessonTxt += sTxt + sep_bar2
                s_start = s_end + len(sep_bar2)
            else:
                s_end = s_start + len(sTxt)
                out_sents.append({'sid': sid, 'text': sTxt, 'start': s_start, 'end': s_end})
                myLessonTxt += sTxt + sep_bar1
                s_start = s_end + len(sep_bar1)
        out_parags.append(out_sents)
        
    # read the questions
    myQstDat = []
    assert p[1].tag == 'QAset'
    q_num = int(p[1].attrib['Num_Ques'])
    
    assert q_num == len(p[1]), 'question num incorrect'
    q_dict = _qst2dat(p[1])
    
    return out_parags, myLessonTxt, q_dict