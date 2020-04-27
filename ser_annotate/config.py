import os
from pathlib import Path

SRC_ROOT = Path(os.path.dirname(os.path.realpath(__file__)))
PROJ_ROOT = SRC_ROOT.parent

DATA_ROOT = PROJ_ROOT / "data"
RESULT_PATH = PROJ_ROOT / "results"

FGC_DEV_RLS = DATA_ROOT / "FGC" / "FGC_release_1.7.13" / "FGC_release_all_dev.json"
FGC_TRAIN_RLS = DATA_ROOT / "FGC" / "FGC_release_1.7.13" / "FGC_release_all_train.json"
FGC_TEST_RLS = DATA_ROOT / "FGC" / "FGC_release_1.7.13" / "FGC_release_all_test.json"

FGC_ANNOT_A = DATA_ROOT / "FGC" / "FGC_annot_1.7.13" / "FGC_release_A_labeled.json"
FGC_ANNOT_B = DATA_ROOT / "FGC" / "FGC_annot_1.7.13" / "FGC_release_B_labeled.json"
FGC_ANNOT_C = DATA_ROOT / "FGC" / "FGC_annot_1.7.13" / "FGC_release_C_labeled.json"