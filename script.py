import os
import json
import requests
import csv
import time
from github import Github
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from dotenv import load_dotenv
from requests.exceptions import ReadTimeout, RequestException
import argparse

# Load environment variables from .env file
load_dotenv()

def load_affiliations(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def load_company_mapping(filepath):
    with open(filepath) as f:
        return json.load(f)

def fetch_with_retries(url, retries=3, timeout=30):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                response_text = response.text[4:]  # Remove XSSI prefix
                return json.loads(response_text)
            else:
                print(f"Failed to fetch data from {url}. Status Code: {response.status_code}")
                return None
        except (ReadTimeout, RequestException) as e:
            if i < retries - 1:
                print(f"Error fetching data from {url}: {str(e)}. Retrying... ({i+1}/{retries})")
                time.sleep(2 ** i)  # Exponential backoff
            else:
                print(f"Max retries reached. Failed to fetch data from {url}")
                return None

def fetch_commits_gerrit(base_url, project, since, until):
    url = f"{base_url}/changes/?q=project:{project}+after:{since}+before:{until}&o=ALL_REVISIONS"
    print(f"Fetching commits from URL: {url}")  # Log URL for debugging
    return fetch_with_retries(url)

def fetch_user_details(base_url, account_id):
    url = f"{base_url}/accounts/{account_id}"
    print(f"Fetching user details from URL: {url}")  # Log URL for debugging
    return fetch_with_retries(url)

def get_repo_metrics_github(repo, affiliations, start_date, end_date):
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

def process_commits_gerrit(base_url, commits, company_mapping):
    committers = set()
    committer_companies = set()
    committer_count = {}

    for commit in commits:
        print(f"Processing commit: {commit.get('id', 'unknown')}")

        if 'owner' in commit and '_account_id' in commit['owner']:
            account_id = commit['owner']['_account_id']
            user_details = fetch_user_details(base_url, account_id)
            if not user_details:
                print(f"Failed to fetch user details for account ID {account_id}. Skipping...")
                continue
            committer = user_details.get('username')
            if not committer:
                print(f"User details for account ID {account_id} do not have a username.")
                continue
        else:
            print(f"Commit {commit.get('id', 'unknown')} does not have an owner with an account ID.")
            continue

        committers.add(committer)

        if committer in company_mapping:
            committer_companies.add(company_mapping[committer])

        if committer in committer_count:
            committer_count[committer] += 1
        else:
            committer_count[committer] = 1

    total_commits = len(commits)
    committers_50 = sorted(committer_count.items(), key=lambda x: x[1], reverse=True)
    commits_50 = sum(x[1] for x in committers_50[:len(committers)//2])
    companies_50 = set(company_mapping.get(committer, 'Unknown') for committer, _ in committers_50[:len(committers)//2])

    return {
        "total_commits": total_commits,
        "total_committers": len(committers),
        "total_committer_companies": len(committer_companies),
        "committers_50_percent_commits": len(committers) // 2,
        "committer_companies_50_percent_commits": len(companies_50)
    }

def write_metrics_to_csv(metrics, output_file):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow([
            "Repository/Project",
            "Total Commits",
            "Total Committers",
            "Total Committer Companies",
            "Committers 50% of Commits",
            "Committer Companies 50% of Commits"
        ])
        # Write the metrics data
        for name, data in metrics.items():
            if "error" in data:
                writer.writerow([name, data["error"]])
            else:
                writer.writerow([
                    name,
                    data.get("num_commits") or data.get("total_commits"),
                    data.get("num_committers") or data.get("total_committers"),
                    data.get("num_committer_companies") or data.get("total_committer_companies"),
                    data.get("num_top_50_percent_committers") or data.get("committers_50_percent_commits"),
                    data.get("num_top_50_percent_committer_companies") or data.get("committer_companies_50_percent_commits")
                ])

def main():
    parser = argparse.ArgumentParser(description="Collect and generate metrics for GitHub or Gerrit repositories.")
    parser.add_argument("--platform", choices=["github", "gerrit"], required=True, help="Specify the platform: 'github' or 'gerrit'.")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format.")
    parser.add_argument("--output-file", default="metrics_output.csv", help="Output CSV file name.")
    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    if args.platform == "github":
        # Constants for GitHub
        ORG_NAME = "anuket-project"
        TOKEN = os.getenv('GITHUB_TOKEN')
        AFFILIATION_FILE = os.path.join(os.path.dirname(__file__), "affiliations.json")

        # Load affiliations
        affiliations = load_affiliations(AFFILIATION_FILE)

        # Initialize Github object
        g = Github(TOKEN)
        org = g.get_organization(ORG_NAME)
        repos = org.get_repos()

        # Collect metrics for all repos
        all_repo_metrics = {}

        for repo in repos:
            try:
                metrics = get_repo_metrics_github(repo, affiliations, start_date, end_date)
                all_repo_metrics[repo.name] = metrics
            except Exception as e:
                print(f"Error processing repo {repo.name}: {e}")
                all_repo_metrics[repo.name] = {"error": str(e)}

        # Write metrics to CSV
        write_metrics_to_csv(all_repo_metrics, args.output_file)

    elif args.platform == "gerrit":
        # Constants for Gerrit
        base_url = "https://gerrit.opnfv.org/gerrit"
        projects = [
            "functest",
            "functest-kubernetes",
            "functest-requirements",
            "functest-xtesting",
            "releng",
            "kuberef",
            "thoth",
            "barometer"
        ]
        COMPANY_MAPPING_FILE = os.path.join(os.path.dirname(__file__), "company_mapping.json")

        # Load company mapping
        company_mapping = load_company_mapping(COMPANY_MAPPING_FILE)

        # Collect metrics for each project
        all_project_metrics = {}

        for project in projects:
            print(f"Fetching commits for project: {project}")
            commits = fetch_commits_gerrit(base_url, project, args.start_date, args.end_date)
            if commits is None:
                print(f"Error: Failed to fetch commits for project {project}")
                all_project_metrics[project] = {"error": "Failed to fetch commits"}
            elif len(commits) == 0:
                print(f"No commits found for project {project}")
                all_project_metrics[project] = {"error": "No commits found"}
            else:
                all_project_metrics[project] = process_commits_gerrit(base_url, commits, company_mapping)

        # Write metrics to CSV
        write_metrics_to_csv(all_project_metrics, args.output_file)

    print(f"Metrics have been written to {args.output_file}")

if __name__ == "__main__":
    main()
