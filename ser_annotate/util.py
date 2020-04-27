import os
import json
from os.path import join

def get_json_in_path(fp):
    files = []
    for file in os.listdir(fp):
        if file.endswith('.json'):
            files.append(data_path+file)
    return files

def read_jsonl(fp):
    out_data = []
    with open(fp) as f:
        for line in f:
            d = json.loads(line)
            out_data.append(d)
    return out_data

def json_load(fp):
    with open(fp) as f:
        return json.load(f)

def json_write(out, out_fp):
    with open(out_fp, 'w') as f:
        json.dump(out, f, indent=4, ensure_ascii=False)
        
def list_fps(fdir, ext=''):
    return [join(fdir, f) for f in os.listdir(fdir) if f.endswith(ext)]