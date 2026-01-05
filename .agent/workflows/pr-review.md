---
description: Review and process open GitHub PRs
---

# GitHub PR Review Workflow

Use this workflow to systematically review and process open PRs.

## Step 1: List Open PRs

```bash
gh pr list --state open
```

## Step 2: For Each PR, Check Status

// turbo
```bash
gh pr view <PR_NUMBER> --json title,state,statusCheckRollup,comments,reviews --jq '{
  title: .title,
  checks: [.statusCheckRollup[] | {name: .name, status: .status, conclusion: .conclusion}],
  commentCount: (.comments | length),
  reviewCount: (.reviews | length)
}'
```

## Step 3: If CI Failed - Check Logs BEFORE Rebasing

> [!CAUTION]
> **NEVER trigger `@dependabot rebase` without first checking the failure logs.**
> Many failures require code changes, not rebases.

// turbo
```bash
gh run view --log-failed --job=<JOB_ID> 2>&1 | tail -50
```

### Common Failure Types

| Failure Pattern | Solution |
|-----------------|----------|
| "Missing required environment variables" | May need rebase to pick up CI fixes |
| "Cannot install... conflicting dependencies" | Dependency conflict - needs manual resolution |
| "ValueError", "ImportError", breaking API changes | Code needs updating, close or fix PR |
| Pre-commit failures (formatting, linting) | Usually fixable, may just need rebase |

## Step 4: Check for Review Comments

// turbo
```bash
gh pr view <PR_NUMBER> --comments --json comments,reviews
```

- Look for `gemini-code-assist` review comments
- Address any suggestions before merging
- If comments suggest code changes, implement them first

## Step 5: Process PR Based on Analysis

### If CI Passed and No Open Comments
```bash
gh pr merge <PR_NUMBER> --merge
```

### If CI Failed Due to Old Base Branch
```bash
gh pr comment <PR_NUMBER> --body "@dependabot rebase"
# Wait 1-2 minutes for Dependabot to rebase
# Then re-check CI status
```

### If CI Failed Due to Code Issues
- Close the PR, or
- Create a fix branch and address the issue

```bash
# To close without merging:
gh pr close <PR_NUMBER> --comment "Closing: <reason>"
```

## Step 6: Update AGENTS.md if Patterns Discovered

If you encounter new patterns or issues, add them to the DON'T section in AGENTS.md.
