import os
from pathlib import Path

SRC_ROOT = Path(os.path.dirname(os.path.realpath(__file__)))
PROJ_ROOT = SRC_ROOT.parent

DATA_ROOT = PROJ_ROOT / "data"
RESULT_PATH = PROJ_ROOT / "results"

FGC_TRAIN_RLS = DATA_ROOT / "FGC" / "FGC_release_1.7.13" / "FGC_release_all_train.json"
FGC_DEV_RLS = DATA_ROOT / "FGC" / "FGC_release_1.7.13" / "FGC_release_all_dev.json"
FGC_TEST_RLS = DATA_ROOT / "FGC" / "FGC_release_1.7.13" / "FGC_release_all_test.json"

FGC_ANNOT_A = DATA_ROOT / "FGC" / "FGC_annot_1.7.13" / "FGC_release_A_labeled.json"
FGC_ANNOT_B = DATA_ROOT / "FGC" / "FGC_annot_1.7.13" / "FGC_release_B_labeled.json"
FGC_ANNOT_C = DATA_ROOT / "FGC" / "FGC_annot_1.7.13" / "FGC_release_C_labeled.json"

SSQA_XML_TRAIN = DATA_ROOT / "SSQA" / "Elementary_Social_Studies_v3.0" / "Train"
SSQA_XML_DEV = DATA_ROOT / "SSQA" / "Elementary_Social_Studies_v3.0" / "Develop"
SSQA_XML_TEST = DATA_ROOT / "SSQA" / "Elementary_Social_Studies_v3.0" / "Test"

# Annotation dir
SSQA_ANNOT = RESULT_PATH / "SSQA_v3.0_annot"

SSQA_OLD_BENCH_TRAIN = DATA_ROOT / "SSQA" / "SSQA_benchmark_v3.2_0312" / "train_202_HumanAnnotation_wLessonText_V.3.2"
SSQA_OLD_BENCH_DEV = DATA_ROOT / "SSQA" / "SSQA_benchmark_v3.2_0312" / "dev_207_HumanAnnotation_wLessonText_V.3.2"
SSQA_OLD_BENCH_TEST = DATA_ROOT / "SSQA" / "SSQA_benchmark_v3.2_0312" / "test_207_HumanAnnotation_wLessonText_V.3.2"