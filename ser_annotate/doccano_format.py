import json
from pathlib import PurePath

from .dataset_reader.io_SSQA import xml2st
from .dataset_reader.io_cano import CanoDict


def ssqa_write_doccano_jsonl(ssqa_xml_fp, out_fdir):
	myFid, parags, lessonTxt, q_dict = xml2st(ssqa_xml_fp)
	# did = PurePath(ssqa_xml_fp).stem
	out_file = out_fdir / (myFid + '.jsonl')
	out_canos = []
	with open(out_file, 'w') as f:
		for qid, qa_pair in q_dict['true-false'].items():
			cano = CanoDict()
			cano.qid = myFid + '-' + qid
			cano.c_text = lessonTxt
			cano.q_text = qa_pair[0]
			cano.a_list.append(qa_pair[1])
			cano.merge_q()
			out_canos.append(cano)
		
		for qid, qa_pair in q_dict['multiple-choice'].items():
			cano = CanoDict()
			cano.qid = myFid + '-' + qid
			cano.c_text = lessonTxt
			cano.q_text = qa_pair[0]
			cano.choices = qa_pair[1]
			cano.a_list = [qa_pair[1][qa_pair[2]]]
			cano.merge_q()
			out_canos.append(cano)
		
		for qid, qa_pair in q_dict['multiple-select'].items():
			cano = CanoDict()
			cano.qid = myFid + '-' + qid
			cano.c_text = lessonTxt
			cano.q_text = qa_pair[0]
			cano.choices = qa_pair[1]
			cano.a_list = [qa_pair[1][i] for i in qa_pair[2]]
			cano.merge_q()
			out_canos.append(cano)
		
		for cano in out_canos:
			json.dump(cano.cano_format, f, ensure_ascii=False)
			f.write('\n')
