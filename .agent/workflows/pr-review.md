---
description: Review and process open GitHub PRs
---

# GitHub PR Review Workflow

Use this workflow to systematically review and process open PRs.

## Step 1: List Open PRs

```bash
gh pr list --state open
```

## Step 2: Wait for AI Review

> [!IMPORTANT]
> Ensure `gemini-code-assist` has reviewed the PR before proceeding.

// turbo
```bash
gh pr view <PR_NUMBER> --json comments,reviews
```

- If no comments yet: **WAIT**. Do not proceed.
- If comments exist: **REVIEW** them. Address valid feedback.

## Step 3: Check Status

// turbo
```bash
gh pr view <PR_NUMBER> --json title,state,statusCheckRollup,comments,reviews --jq '{
  title: .title,
  checks: [.statusCheckRollup[] | {name: .name, status: .status, conclusion: .conclusion}],
  commentCount: (.comments | length),
  reviewCount: (.reviews | length)
}'
```

## Step 4: Check Logs BEFORE Rebasing

> [!CAUTION]
> **NEVER trigger `@dependabot rebase` without first checking failure logs.**

// turbo
```bash
gh pr checks <PR_NUMBER> --log | tail -50
```



## Step 5: Process PR

### If CI Passed and No Open Comments
```bash
gh pr merge <PR_NUMBER> --merge
```

### If CI Failed Due to Old Base Branch
```bash
gh pr comment <PR_NUMBER> --body "@dependabot rebase"
```

### If CI Failed Due to Code Issues

> [!CAUTION]
> **NEVER close a PR without explicit user approval.**

1. Notify user & request approval
2. Create tracking issue
3. Close PR

```bash
# Create GitHub issue to track the blocked upgrade
gh issue create --title "Blocked: <package> <old> → <new>" \
  --body "## Problem
<description>

## Fix Path
<steps>

## Related
- Closed PR #<N>" \
  --label "dependencies,blocked"

# Then close the PR
gh pr comment <PR_NUMBER> --body "<explanation>"
gh pr close <PR_NUMBER>
```

## Step 6: Update Documentation

If you encounter new patterns, add them to `AGENTS.md`.
