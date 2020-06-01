from .std import *
from .dataset_reader.io_cano import CrpCano
from .dataset_reader.io_SSQA import str_lesson2st

def annot2se(annot_fp):
	'''
	Convert annotated file to supporting evidence file.
	Use keyword positions to determine which sentences are supporting sentences.
	'''
	def has_keyword(s, labels):
		for label in labels:
			assert label[2] == 'Keyword'
			l_start = label[0]
			l_end = label[1]
			if s[0] <= l_start <= s[1]:
				assert s[0] <= l_end <= s[1], 'keyword cross sentence!!'
				return True
		return False
	
	annots = jseq_load(annot_fp)
	myCrpCano = CrpCano()
	myCrpCano.load_annot_ssqa(annots)
	out_q_list = []
	for qid, q_annot in myCrpCano.items():
		se = []
		st_parags = str_lesson2st(q_annot.c_text)
		
		# Detect "No SE"
		if q_annot.labels[0][0] == 0:
			out_q_list.append({'qid': qid, 'qtext': q_annot.qtext, 'context': st_parags, 'se': se})
			continue
		for p_i, p in enumerate(st_parags):
			for s_i, s in enumerate(p[2]):
				if has_keyword(s, q_annot.labels):
					se.append([p_i, s_i])
					assert se, "No supporting evidence in qid:{}".format(qid)
		out_q_list.append({'qid': qid, 'qtext': q_annot.qtext, 'context': st_parags, 'se': se})
	return out_q_list