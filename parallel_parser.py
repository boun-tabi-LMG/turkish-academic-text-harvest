import logging
from tika import parser
from multiprocessing import Pool
from argparse import ArgumentParser
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def parse_file(file_path, output_dir):
    """
    Extracts text content from a PDF file and writes it to a text file.

    Args:
        file_path (Path): The path to the input PDF file.
        output_dir (Path): The output folder path where the text file will be saved.
    """
    try:
        content = parser.from_file(str(file_path))['content']
        logger.info(f"Parsing: {file_path}")
        with open(output_dir / f'{file_path.stem}.txt', 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error while parsing {file_path}: {e}")

def parse_scanned_file(file_path, output_dir):
    try:
        elements = partition_pdf(str(file_path), strategy="fast")
        df = convert_to_dataframe(elements)
        df.to_csv(output_dir / f'{file_path.stem}.csv')
    except Exception as e:
        logger.error(f"Error while parsing {file_path}: {e}")
        
def main():
    arg_parser = ArgumentParser(description='Performs OCR on PDF files in the given path.')
    arg_parser.add_argument('-i', '--input', type=str, help='The path to the PDF folder.', required=True)
    arg_parser.add_argument('-o', '--output', type=str, help='The output folder.')
    arg_parser.add_argument('-n', '--num_threads', type=int, help='The number of threads to use.', default=4)
    arg_parser.add_argument('-t', '--tool', choices=['tika', 'unstructured'], help='The tool to use.', default='tika')
    args = arg_parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Number of threads: {args.num_threads}")

    with Pool(args.num_threads) as pool:
        parse_fn = parse_file if args.tool == 'tika' else parse_scanned_file
        pool.starmap(parse_fn, [(file_path, output_dir) for file_path in input_dir.iterdir()])

if __name__ == "__main__":
    main()
