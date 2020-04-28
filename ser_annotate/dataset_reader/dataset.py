from tqdm import tqdm
import stanza
from opencc import OpenCC

NER_TYPES = ['PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE',
            'DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']

nlp = stanza.Pipeline('zh', processors='tokenize, ner')
cc = OpenCC('t2s')

class CanoDict:
    def __init__(self):
        self.qid:str
        self.text: str
        self.q_text: str
        self.c_text: str
        self.a_list = []
        self.labels = []
        self.choices = []
    
    @property
    def meta(self):
        if self.choices:
            return {'qid': self.qid, 'qtext': self.q_text, 'choices': str(self.choices), 'answer': str(self.a_list)}
        else:
            return {'qid': self.qid, 'qtext': self.q_text, 'answer': str(self.a_list)}
        
    @property
    def cano_format(self):
        return {'text': self.text, 'labels': self.labels, 'meta': self.meta}
    
    def remove_illegal_labels(self):
        def is_overlap(label, corrected_labels):
            label_cover = [i for i in range(label[0], label[1])]
            for c_label in corrected_labels:
                c_label_cover = [i for i in range(c_label[0], c_label[1])]
                for c_cover_i in c_label_cover:
                    if c_cover_i in label_cover:
                        return True
            return False
        
        corrected_labels = []
        for label in self.labels:
            if not is_overlap(label, corrected_labels):
                corrected_labels.append(label)
        self.labels = corrected_labels
        
    def merge_q(self):
        offset = len(self.q_text) + 1 # +1 for '\n' token
        
        for label in self.labels:
            label[0] += offset
            label[1] += offset
        self.text = self.q_text + '\n' + self.c_text
        
    def merg_q_ie(self):
        doc = nlp(cc.convert(self.q_text))
        for s in doc.sentences:
            for e in s.ents:
                etype = e.type
                assert etype in NER_TYPES
                self.labels.append([e.start_char, e.end_char, etype])
            

class CrpCano(dict):
    def __init__(self, *args, **kwargs):
        super(CrpCano, self).__init__(*args, **kwargs)
        
    def load_rls(self, rls_all):
        for d in tqdm(rls_all):
            cano_dict = CanoDict()
            cano_dict.c_text = d['DTEXT']
            rls_q = d['QUESTIONS'][0]
            qid = rls_q['QID']
            cano_dict.qid = qid
            cano_dict.q_text = rls_q['QTEXT']
            atokens = [atoken['text'] for a in rls_q['ANSWER'] for atoken in a['ATOKEN']]
            cano_dict.a_list = [a['ATEXT'] for a in rls_q['ANSWER']]
            if 'ASPAN' not in rls_q:
                keywords = []
            else:
                keywords = rls_q['ASPAN']

            for keyword in keywords:
                if keyword['text'] in atokens:
                    cano_dict.labels.append([keyword['start'], keyword['end'], 'Answer'])
                else:
                    cano_dict.labels.append([keyword['start'], keyword['end'], 'Keyword'])

            cano_dict.remove_illegal_labels()
            cano_dict.merge_q()
            cano_dict.merg_q_ie()
            self[qid] = cano_dict
                    
    def load_annot(self, annot_all):
        for annot in annot_all:
            cano_dict = CanoDict()
            qid = annot['text'][:7]
            
            label_set = set()
            for label_annot in annot['annotations']:
                label = label_annot['label']
                start = label_annot['start_offset']
                end = label_annot['end_offset']
                label_set.add((start, end, "Keyword"))

            cano_dict.text = annot['text'][shift]
            cano_dict.labels = [[label[0], label[1], label[2]] for label in label_set]
            cano_dict.meta['qid'] = qid
            self[qid] = cano_dict
            
    def merge_rls(self, rls_all):
        rls_all_dict = {d['QUESTIONS'][0]['QID']: d for d in rls_all}
        for qid, cano_dict in self.items():
            rls_q = rls_all_dict[qid]['QUESTIONS'][0]
            cano_dict.meta['question'] = rls_q['QTEXT']
            cano_dict.meta['answer'] = [a['ATEXT'] for a in rls_q['ANSWER']]
            cano_dict.meta['atype'] = rls_q['ATYPE_']
            

    
    