# Recommendation System Project

This project is a tourism recommendation system built with Python and Flask.

## Description

It includes:
- Demographic recommendation based on user profile.
- Content-based recommendation using user preferences.
- Collaborative recommendation using Pearson similarity.
- Group recommendation aggregation.
- A Flask web interface for registration, login, dashboard, and favorites management.
- Helper scripts for data initialization, image downloading, and description generation.
- Evaluation of recommendation systems with metrics and plots.

## Project structure

- `app/`: main Flask application package.
  - `__init__.py`: Flask application and SQLAlchemy initialization.
  - `models.py`: data models.
  - `routes.py`: web routes and application logic.
  - `utils.py`: recommendation merging utilities.
  - `data_processor.py`: initial data loading from text files.
  - `demographic_recommendation.py`: demographic recommendation logic.
  - `content_based_recommendation.py`: content-based recommendation logic.
  - `collaborative_recommendation.py`: collaborative recommendation logic.
  - `group_recommendation.py`: group recommendation logic.
  - `static/`: static resources, data, and descriptions.
  - `templates/`: HTML templates.

- `scripts/`: helper scripts.
  - `download_images.py`: downloads images for items.
  - `crawl_descriptions.py`: fetches item descriptions from Wikipedia.
  - `reduce_images.py`: optimizes PNG images.
  - `evaluate.py`: evaluates recommendation systems and generates results.

- `config.py`: application configuration.
- `run.py`: Flask app entry point.
- `instance/`: generated SQLite database.
- `metrics/`: generated evaluation metrics and reports.

## Installation

1. Create a virtual environment:

```bash
python -m venv env
```

2. Activate the environment:

```powershell
env\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Initialize the database and load sample data:

```bash
python -c "from app.data_processor import initialize_database; initialize_database()"
```

2. Run the Flask application:

```bash
python run.py
```

3. Open your browser at `http://127.0.0.1:5000`.

## Available scripts

- `python scripts/evaluate.py`: generates evaluation metrics and plots in the `metrics/` folder.
- `python scripts/download_images.py`: downloads item images from Google.
- `python scripts/crawl_descriptions.py`: generates item descriptions using Wikipedia.
- `python scripts/reduce_images.py app/static/images`: optimizes PNG images in the specified folder.

## Notes

- The SQLite database is stored at `instance/users.db`.
- The project uses sample data included in `app/static/data/`.
- Generated database and result files are excluded from the repository via `.gitignore`.
- This implementation is a proof of concept for recommendation algorithms and is not production-ready.

## Database initialization details

The command above loads the data tables in the database from the provided text files, including users, items, occupations, preferences, item classifications, and ratings.

It does not automatically download or generate image files or Wikipedia descriptions. To populate images and descriptions, run the corresponding helper scripts after the database is initialized.

If `instance/users.db` already exists, remove it first to recreate the database from scratch:

```bash
rm -r instance
python -c "from app.data_processor import initialize_database; initialize_database()"
```