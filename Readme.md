# GitHub Repository Metrics Collector for Anuket Projects


This Python script collects various metrics from repositories in a GitHub organization over a specified timeframe. The script leverages the GitHub API and can be customized to analyze metrics for different organizations and time periods. Additionally, it can identify the affiliations of committers using a predefined JSON file.

## Features

- Number of Commits: Total number of commits within the specified timeframe.
-  Number of Committers: Unique committers contributing to the repositories.
- Number of Committer Companies: Companies affiliated with the committers.
- Top 50% Committers: Top 50% of committers based on the number of commits.
- Top 50% Committer Companies: Companies affiliated with the top 50% committers.



## Requirements
- Python 3.12.3+
- GitHub Access Token with repository read permissions
- PyGithub library
- python-dotenv library
- JSON file containing committer affiliations

## Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

2. Install required Python libraries:
```bash
pip install PyGithub python-dotenv
```

3. Create a .env file:
- Create a .env file in the root directory of the project.
- Add your GitHub token to the file:
```bash
GITHUB_TOKEN=your_github_token
```

4. Create an affiliations.json file:
- Create a JSON file named affiliations.json in the root directory.
- The file should map GitHub usernames to their company affiliations. Example:
```bash
{
  "user1": "Company A",
  "user2": "Company B",
  "user3": "Company C"
}
```

## Usage
1. Run the script:
```bash
python script_name.py
```

2. Output:
- The script will output a JSON structure containing the metrics for each repository in the specified GitHub organization.
- Adjust the TIMEFRAME_DAYS constant in the script to change the timeframe (e.g., 60 for the last two months).
