import kenlm
import pandas as pd
from transformers import PreTrainedTokenizerFast
from normalize import preprocess_text
import argparse
from pathlib import Path
from vnlp import SentenceSplitter
from pyinstrument import Profiler
from multiprocessing import Pool
import logging
#import langid

logger = logging.getLogger(__name__)
level = logging.INFO
logger.setLevel(level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# handler for console info messages
ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(level)
logger.addHandler(ch)

# handler for file info messages
fh = logging.FileHandler('log.txt')
fh.setFormatter(formatter)
fh.setLevel(level)
logger.addHandler(fh)

tokenizer = PreTrainedTokenizerFast.from_pretrained('/media/disk/home/zeynep.yirmibesoglu/VBARTTokenizer')
model=kenlm.Model("/media/disk/home/zeynep.yirmibesoglu/kenlm/tr_wiki_spiece_5gram.binary")
sentence_splitter = SentenceSplitter()

def is_turkish_content(text):
    """
    Determines if the given text is in Turkish.

    Returns:
        bool: True if the text is in Turkish, False otherwise.
    """
    try:
        # detected_language = detect(text) # lower() yaparsak langdetect basliklara isimlere turkce diyor, yoksa onlardan kurtulabiliyoruz.
        detected_language = langid.classify(text)[0]
        if detected_language == 'tr':
            return True
        else:
            return False
    except:
        return False

def split_score(file):
	logger.info(f'Scoring {file}')
	with open(file, encoding="utf-8") as extracted_file:
		text = extracted_file.read()
	# text = preprocess_text(text)
	sentences = sentence_splitter.split_sentences(text)
	df = pd.DataFrame()
	for i, sentence in enumerate(sentences):
		if len(sentence.split(" ")) > 3:
			lower_sentence = sentence.lower().strip()
			tokens = tokenizer.tokenize(lower_sentence)
			tokenized_sentence = " ".join(tokens)
			df.loc[i, 'line'] = sentence
			df.loc[i, 'token_count'] = len(tokens)
			df.loc[i, 'tokenized_line'] = tokenized_sentence
			#df.loc[i, 'perplexity'] = model.perplexity(tokenized_sentence)
			#df.loc[i, 'is_turkish'] = is_turkish_content(sentence)
			df.loc[i, 'lm_score'] = model.score(tokenized_sentence, bos = True, eos = True)
			df.loc[i, 'lm_score_div'] = df.loc[i, 'lm_score'] / df.loc[i, 'token_count']
	
	file_path = Path(file)

	scored_folder = file_path.parent.parent / "scored_csv"
	scored_filename = scored_folder / file_path.name.replace('_no_inline_citations.txt', '_scored.csv')

	df.to_csv(scored_filename, encoding='utf-8', index=False)
	logger.info(f'Finished scoring {file}, generated {str(scored_filename)}')

def main():
	arg_parser = argparse.ArgumentParser(description='Splits, normalizes and scores extracted text')
	arg_parser.add_argument('-p', '--path', type=str, help='The path to the TXT folder or file.', required=True)
	arg_parser.add_argument('-n', '--num_threads', type=int, help='The number of threads to use.', default=4)
	arg_parser.add_argument('-s', '--skip',  action='store_true', help='Skip files that already exist in the output directory.')
	args = arg_parser.parse_args()

	input_path = Path(args.path)
	if input_path.is_file() and input_path.name.endswith('.txt'):
		input_files = [str(input_path)]
	elif input_path.is_dir():
		input_files = [str(f) for f in input_path.iterdir() if f.name.endswith('.txt')]
	
	scored_folder = input_path.parent / "scored_csv"
	scored_folder.mkdir(parents=True, exist_ok=True)

	if args.skip: 
		output_files = [f.name.replace('_scored.csv', '_no_inline_citations.txt') for f in scored_folder.iterdir()]
		input_files = [str(input_file) for input_file in input_files if Path(input_file).name not in output_files]

	logger.info(f'{len(input_files)} will be processed with {args.num_threads} threads')
	with Pool(args.num_threads) as pool:
		pool.map(split_score, input_files)

	"""with Profiler(interval=0.1) as profiler:
		for file in input_files:
			split_score(file)
	profiler.print()"""
	
if __name__ == '__main__':
    main()
