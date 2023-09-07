import kenlm
import pandas as pd
from transformers import PreTrainedTokenizerFast
from normalize import preprocess_text
import argparse
from pathlib import Path
from vnlp import SentenceSplitter
from pyinstrument import Profiler
#import langid

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

def normalize_split_score(file):
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
	scored_folder.mkdir(parents=True, exist_ok=True)
	scored_filename = scored_folder / file_path.name.replace('_no_inline_citations.txt', '_scored.csv')

	df.to_csv(scored_filename, encoding='utf-8', index=False)

def main():
	arg_parser = argparse.ArgumentParser(description='Splits, normalizes and scores extracted text')
	arg_parser.add_argument('-p', '--path', type=str, help='The path to the TXT folder or file.', required=True)
	args = arg_parser.parse_args()

	input_path = Path(args.path)
	if input_path.is_file() and input_path.name.endswith('.txt'):
		input_files = [str(input_path)]
	elif input_path.is_dir():
		input_files = [str(f) for f in input_path.iterdir() if f.name.endswith('.txt')]
		
	with Profiler(interval=0.1) as profiler:
		for file in input_files:
			normalize_split_score(file)
	profiler.print()
	
if __name__ == '__main__':
    main()
