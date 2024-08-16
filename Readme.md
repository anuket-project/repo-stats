# Anuket Project Repository Statistics

## Features

- Collects commit data from both GitHub and Gerrit repositories.
- Generates metrics such as the number of commits, committers, and committer companies.
- Analyzes the top 50% of committers by commit count.
- Outputs metrics to a CSV file for easy analysis.

## Setup

## Requirements
- Python 3.12.3 or later
- A GitHub token with access to the Anuket Project repositories
- Access to the Gerrit server for Anuket Project

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Create a .env file:
- Create a .env file in the root directory of the project.
- Add your GitHub token to the file:
```bash
GITHUB_TOKEN=your_github_token
```

4. Prepare the required JSON files:

- affiliations.json:Contains mapping of committers to their affiliations (GitHub).
- company_mapping.json: Contains mapping of Gerrit users to their companies.

Place these files in the root directory of the project.

## Usage
### Command-line Arguments
- --platform: Specify the platform (github or gerrit).
- --start-date: Start date for collecting commits (format: YYYY-MM-DD).
- --end-date: End date for collecting commits (format: YYYY-MM-DD).
- --output-file: Name of the output CSV file (default: metrics_output.csv).

## Example Commands
### GitHub:
```bash
python main.py --platform github --start-date 2024-01-01 --end-date 2024-07-31 --output-file github_metrics.csv
```

### Gerrit:
```bash
python main.py --platform gerrit --start-date 2024-01-01 --end-date 2024-07-31 --output-file gerrit_metrics.csv
```

## Output:

The script generates a CSV file containing the following columns:

- Repository/Project
- Total Commits
- Total Committers
- Total Committer Companies
- Committers 50% of Commits
- Committer Companies 50% of Commits
