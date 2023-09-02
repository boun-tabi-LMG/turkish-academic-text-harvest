import os, random

bounllm_dir = '/media/disk/datasets/bounllm'
dergipark_dir = os.path.join(bounllm_dir, 'dergipark/txt')
dergipark_files = os.listdir(dergipark_dir)
random.shuffle(dergipark_files)
yok_tez_dir = os.path.join(bounllm_dir, 'yok-tez/txt')
yok_tez_files = os.listdir(yok_tez_dir)
random.shuffle(yok_tez_files)
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR_dergipark = os.path.join(THIS_DIR, 'sample-dergipark')
if not os.path.exists(SAMPLE_DIR_dergipark):
    os.makedirs(SAMPLE_DIR_dergipark)
SAMPLE_DIR_yok_tez = os.path.join(THIS_DIR, 'sample-yok-tez')
if not os.path.exists(SAMPLE_DIR_yok_tez):
    os.makedirs(SAMPLE_DIR_yok_tez)
for el in dergipark_files[:1000]:
    os.symlink(os.path.join(dergipark_dir, el), os.path.join(SAMPLE_DIR_dergipark, el))
for el in yok_tez_files[:1000]:
    os.symlink(os.path.join(yok_tez_dir, el), os.path.join(SAMPLE_DIR_yok_tez, el))