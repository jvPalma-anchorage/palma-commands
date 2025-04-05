from prs.config import get
from prs.vc_tools.github.client import list_pull_request_ids, get_pull_request_details
from prs.vc_tools.github.adapter import to_model
from prs.utils.formatting import OutputBuilder, color_text

# Predefined label categories
DANG_LIST = ["skip-ci", "conflict", "do-not-merge", "no-reviewers"]
GOOD_LIST = ["ready-after-ci", "ready-to-merge", "deploy-pr-backoffice", "deploy-pr-frontoffice"]

def compute_checks_status(pr):
    total = 0
    success_count = 0
    pending_count = 0
    failing_count = 0
    for check in pr.checks:
        state = check.get("state", "").upper()
        if state:
            total += 1
            if state == "SUCCESS":
                success_count += 1
            elif state in ["FAILURE", "FAILED"]:
                failing_count += 1
            elif state == "PENDING":
                pending_count += 1
    if total == 0:
        # No tests available, default to yellow
        return "CHKS", "yellow"
    if failing_count > 0:
        return "CHKS", "red"
    elif pending_count > 0:
        return "CHKS", "yellow"
    else:
        return "CHKS", "green"

def compute_reviews_status(pr):
    approved = False
    if pr.reviews:
        for review in pr.reviews:
            if review.get("state", "").upper() == "APPROVED":
                approved = True
                break
    return "RVWS", "green" if approved else "yellow"

def compute_labels_status(pr):
    # If any label is in DANG_LIST, mark as red
    for label in pr.labels:
        if label in DANG_LIST:
            return "LABL", "red"
    # Else if any label is in GOOD_LIST, mark as green
    for label in pr.labels:
        if label in GOOD_LIST:
            return "LABL", "green"
    # Otherwise, yellow
    return "LABL", "yellow"

def compute_open_status(pr):
    # Since we list only open PRs, use green unless it's a draft
    return "OPEN", "yellow" if pr.isDraft else "green"

def compute_author_status(pr):
    config_username = get("git", "username")
    return pr.author, "green" if pr.author == config_username else "cyan"

def list_pull_requests(options: dict):
    """
    Fetches pull requests and displays them with a detailed summary.
    The summary has two lines per PR:
      1. First line: PR number (gray-2), title (blue), and author (green if own, else cyan)
      2. Second line: A tab-indented line with:
            [OPEN] [RVWS] [CHKS] [LABL] Username
         Each bracket is colored based on conditions.
    """
    config_username = get("git", "username")
    filters = {"author": config_username, "state": "open", "include_draft": options.get("include_draft", False)}
    pr_refs = list_pull_request_ids(filters)
    all_prs = []

    print(f"prs: {pr_refs}")
    for pr_id, source_tag, is_draft in pr_refs:
        raw = get_pull_request_details(pr_id)
        pr_model = to_model(raw)
        pr_model.source = source_tag
        # Ensure the model reflects draft status
        pr_model.isDraft = is_draft
        all_prs.append(pr_model)

    ob = OutputBuilder()

    for pr in all_prs:
        # First summary line:
        pr_number = color_text(f"#{pr.id}", "gray-2")
        pr_title = color_text(pr.title, "blue")
        author_color = "green" if pr.author == config_username else "cyan"
        pr_author = color_text(pr.author, author_color)
        ob.add_line(f"{pr_number} {pr_title} {pr_author}")

        # Second summary line:
        open_text, open_color = compute_open_status(pr)
        reviews_text, reviews_color = compute_reviews_status(pr)
        checks_text, checks_color = compute_checks_status(pr)
        labels_text, labels_color = compute_labels_status(pr)
        summary_author, summary_author_color = compute_author_status(pr)

        summary_line = "\t" + " ".join([
            color_text(f"[{open_text}]", open_color),
            color_text(f"[{reviews_text}]", reviews_color),
            color_text(f"[{checks_text}]", checks_color),
            color_text(f"[{labels_text}]", labels_color),
            color_text(summary_author, summary_author_color)
        ])
        ob.add_line(summary_line)
        ob.add_line("")  # Blank line between PRs

    print(ob.get_output())
