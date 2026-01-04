"""Build GitHub search queries from user parameters."""

from typing import List, Optional


def build_search_query(
    mode: str,
    repo: Optional[str] = None,
    skills: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    language: Optional[str] = None,
    difficulty: Optional[str] = None,
    labels: Optional[List[str]] = None,
    state: str = "open"
) -> str:
    """
    Build a GitHub search query string.
    
    Args:
        mode: "repo" or "global"
        repo: Repository name in "owner/repo" format (required if mode="repo")
        skills: List of skills/keywords to search for
        topics: List of topics to search for
        language: Programming language filter
        difficulty: Difficulty level (good-first-issue, easy, medium, hard)
        labels: Additional labels to filter by
        state: Issue state (open, closed, all)
        
    Returns:
        GitHub search query string
    """
    query_parts = ["is:issue"]
    
    # Add state filter
    if state and state != "all":
        query_parts.append(f"is:{state}")
    
    # Add repository scope
    if mode == "repo" and repo:
        query_parts.append(f"repo:{repo}")
    
    # Add difficulty labels
    if difficulty:
        if difficulty == "good-first-issue":
            query_parts.append('label:"good first issue"')
        elif difficulty == "easy":
            # Try common variations of easy labels
            query_parts.append('(label:"good first issue" OR label:easy OR label:beginner)')
        elif difficulty == "medium":
            query_parts.append('(label:medium OR label:intermediate)')
        elif difficulty == "hard":
            query_parts.append('(label:hard OR label:advanced OR label:expert)')
    
    # Add custom labels
    if labels:
        for label in labels:
            query_parts.append(f'label:"{label}"')
    
    # Add language filter
    if language:
        query_parts.append(f"language:{language}")
    
    # Build keyword search from skills and topics
    keywords = []
    if skills:
        keywords.extend(skills)
    if topics:
        keywords.extend(topics)
    
    # Add keywords as general search terms
    if keywords:
        # Join keywords with OR for broader matching
        keyword_query = " ".join(keywords)
        query_parts.append(keyword_query)
    
    return " ".join(query_parts)


def explain_query(query: str) -> List[str]:
    """
    Explain how a query matches issues.
    
    Args:
        query: The GitHub search query
        
    Returns:
        List of human-readable explanations
    """
    explanations = []
    
    if "is:issue" in query:
        explanations.append("Searching for issues")
    
    if "is:open" in query:
        explanations.append("Only open issues")
    elif "is:closed" in query:
        explanations.append("Only closed issues")
    
    if "repo:" in query:
        repo = query.split("repo:")[1].split()[0]
        explanations.append(f"In repository: {repo}")
    
    if "good first issue" in query.lower():
        explanations.append("Good for beginners")
    
    if "language:" in query:
        lang = query.split("language:")[1].split()[0]
        explanations.append(f"Primary language: {lang}")
    
    if "label:" in query:
        explanations.append("Filtered by specific labels")
    
    return explanations


def score_result(issue_data: dict, query_params: dict) -> List[str]:
    """
    Generate score reasons for why an issue matched the search.
    
    Args:
        issue_data: GitHub issue data
        query_params: Original search parameters
        
    Returns:
        List of match reasons
    """
    reasons = []
    
    labels = [label.get("name", "").lower() for label in issue_data.get("labels", [])]
    
    # Check difficulty match
    difficulty = query_params.get("difficulty", "")
    if difficulty == "good-first-issue" and "good first issue" in labels:
        reasons.append("Label match: good first issue")
    
    # Check custom label matches
    custom_labels = query_params.get("labels") or []
    for label in custom_labels:
        if label.lower() in labels:
            reasons.append(f"Label match: {label}")
    
    # Check skill/topic keyword matches
    title = issue_data.get("title", "").lower()
    body = issue_data.get("body", "").lower() if issue_data.get("body") else ""
    
    skills = query_params.get("skills") or []
    for skill in skills:
        if skill.lower() in title or skill.lower() in body:
            reasons.append(f"Keyword match: {skill}")
    
    topics = query_params.get("topics") or []
    for topic in topics:
        if topic.lower() in title or topic.lower() in body:
            reasons.append(f"Topic match: {topic}")
    
    # Check language match
    if query_params.get("language"):
        # This is harder to verify from issue data, but we can note it was requested
        reasons.append(f"Repository language filter: {query_params['language']}")
    
    # If no specific reasons, add general match
    if not reasons:
        reasons.append("General search match")
    
    return reasons