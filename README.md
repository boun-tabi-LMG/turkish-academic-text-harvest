# turkish-academic-text-harvest

This repository contains scripts for downloading articles from Dergipark, a Turkish academic website, as well as Turkish theses. It provides functionality to convert PDF files to text and filter them to produce a dataset for further analysis and research.

The repository is organized into the following directories:

- **`scrapers/`**: This directory contains scripts for scraping content from Dergipark and the Turkish National Thesis Center. It helps acquire relevant academic materials.
- **`extractors/`**: This directory includes tools for text extraction from PDF documents.
    - **`parallel_parser.py`**: This script extracts text from PDFs concurrently, improving the process's efficiency.
    - **`extractor.py`**: It extracts and filters text from either PDF files or pre-parsed texts, preparing the text for further analysis.
    - **`kenlm_score.py`**: This script uses a KenLM language model to score sentences within the documents, assisting in evaluating their linguistic quality.