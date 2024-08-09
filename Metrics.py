import os
from github import Github
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import json
from dotenv import load_dotenv

def load_affiliations(affiliation_file):
    with open(affiliation_file, 'r') as file:
        return json.load(file)

def get_repo_metrics(repo, affiliations, start_date, end_date):
    commits = repo.get_commits(since=start_date, until=end_date)
    commit_data = []

    for commit in commits:
        commit_author = commit.author.login if commit.author else 'unknown'
        commit_data.append({
            'sha': commit.sha,
            'author': commit_author,
            'date': commit.commit.author.date,
        })

    # Number of commits
    num_commits = len(commit_data)

    # Number of committers
    committers = set([commit['author'] for commit in commit_data])
    num_committers = len(committers)

    # Number of committer companies
    committer_companies = set([affiliations.get(commit['author'], 'unknown') for commit in commit_data])
    num_committer_companies = len(committer_companies)

    # Top 50% committers by commits
    commit_count_by_committer = defaultdict(int)
    for commit in commit_data:
        commit_count_by_committer[commit['author']] += 1

    sorted_committers = sorted(commit_count_by_committer.items(), key=lambda item: item[1], reverse=True)
    top_50_percent_committers = sorted_committers[:len(sorted_committers) // 2]
    num_top_50_percent_committers = len(top_50_percent_committers)

    # Number of committer companies for top 50% committers
    top_50_percent_committer_companies = set([affiliations.get(committer[0], 'unknown') for committer in top_50_percent_committers])
    num_top_50_percent_committer_companies = len(top_50_percent_committer_companies)

    # Output the metrics
    metrics = {
        "num_commits": num_commits,
        "num_committers": num_committers,
        "num_committer_companies": num_committer_companies,
        "num_top_50_percent_committers": num_top_50_percent_committers,
        "num_top_50_percent_committer_companies": num_top_50_percent_committer_companies,
    }
    
    return metrics

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Constants
    ORG_NAME = "anuket-project"
    TOKEN = os.getenv('GITHUB_TOKEN')
    TIMEFRAME_DAYS = 365  # Change this to filter the timeframe, e.g., 60 for last 2 months
    AFFILIATION_FILE = os.path.join(os.path.dirname(__file__), "affiliations.json")

    # Load affiliations
    affiliations = load_affiliations(AFFILIATION_FILE)

    # Initialize Github object
    g = Github(TOKEN)
    org = g.get_organization(ORG_NAME)
    repos = org.get_repos()

    # Calculate timeframe
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=TIMEFRAME_DAYS)

    # Collect metrics for all repos
    all_repo_metrics = {}

    for repo in repos:
        try:
            metrics = get_repo_metrics(repo, affiliations, start_date, end_date)
            all_repo_metrics[repo.name] = metrics
        except Exception as e:
            print(f"Error processing repo {repo.name}: {e}")

    # Output the metrics for all repos
    print(json.dumps(all_repo_metrics, indent=4))

if __name__ == "__main__":
    main()
