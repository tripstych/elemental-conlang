# Elemental Conlang Project

A comprehensive constructed language toolkit that analyzes words through elemental associations and generates translation dictionaries.

## Installation

### Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

### NLTK Data Setup

After installing dependencies, download required NLTK data:

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger'); nltk.download('omw-1.4')"
```

### spaCy Model

Download the English language model:

```bash
python -m spacy download en_core_web_lg
```

## Quick Start

### 1. Build Elemental Dictionary

Your first step if you're starting without any .json files for data:

```bash
python build_elemental_dictionary.py
```

This is the core semantic categorization engine, currently configured to quantize 'elemental' aspects of words (e.g., "creative" has a high fire quotient).

### 2. Generate Translation Dictionary

Next, run the logo gene script:

    python logo_gene.py

for you translation dictionary 'elemental_dict.json'