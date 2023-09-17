import os
import argparse
import logging

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=os.path.join(THIS_DIR, 'check_empty.log'), filemode='a')


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--path', type=str, default=THIS_DIR)
args = parser.parse_args()


def check_empty(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    if content == '':
        return True
    else:
        return False


if __name__ == '__main__':
    if not os.path.exists(args.path):
        print('Path does not exist!')
        exit(1)
    if os.path.isdir(args.path):
        dir = args.path
        txt_files = [f for f in os.listdir(dir) if f.endswith('.txt')]
    elif os.path.isfile(args.path):
        dir = os.path.dirname(args.path)
        txt_files = [args.path]
    for txt_file in txt_files:
        path = os.path.join(dir, txt_file)
        empty = check_empty(path)
        if empty:
            logger.info('Empty file: {}'.format(path))
            os.remove(path)
