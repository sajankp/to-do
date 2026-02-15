---
description: Review and process open GitHub PRs
---

# GitHub PR Review Workflow

Use this workflow to systematically review and process open PRs.

## 🧭 When to Use This Workflow

```
Do I have open PRs to process?
├── YES → Use this workflow
└── NO → Is there a new PR from Dependabot/other?
         └── Run `gh pr list --state open` to check
```

---

## Step 1: List Open PRs

```bash
gh pr list --state open
```

## Step 2: Wait for AI Review

> [!IMPORTANT]
> Ensure `gemini-code-assist` has reviewed the PR before proceeding.

// turbo
```bash
# Check specifically for gemini-code-assist review
gh api repos/:owner/:repo/pulls/<PR_NUMBER>/reviews \
  --jq '[.[] | select(.user.login == "gemini-code-assist" and .state != "PENDING")] | length'

# Also check for any inline or general comments
gh api repos/:owner/:repo/pulls/<PR_NUMBER>/comments --jq 'length'
gh api repos/:owner/:repo/issues/<PR_NUMBER>/comments --jq 'length'
```

- If all counts are 0: **WAIT**.
- If any count > 0: Proceed to Step 2.1.

### Step 2.1: Fetch Feedback Details

If feedback exists, fetch the details to analyze:

```bash
# 1. Fetch Formal Reviews (Approve/Request Changes)
gh api repos/:owner/:repo/pulls/<PR_NUMBER>/reviews --jq '.[] | {state: .state, author: .user.login, body: .body}'

# 2. Fetch Inline Code Comments
gh api repos/:owner/:repo/pulls/<PR_NUMBER>/comments --jq '.[] | {path: .path, line: .line, author: .user.login, body: .body}'

# 3. Fetch General Conversation Comments
gh api repos/:owner/:repo/issues/<PR_NUMBER>/comments --jq '.[] | {author: .user.login, body: .body}'
```

### Step 2.2: Critically Evaluate Feedback

> [!IMPORTANT]
> **Do NOT blindly accept AI review comments.** Think critically about each suggestion.

For each review comment, ask yourself:

**1. Does this improve the code?**
- ✅ Better design/architecture
- ✅ Follows project conventions
- ✅ Fixes actual bugs
- ❌ Subjective style preference
- ❌ Contradicts documented patterns

**2. What's the trade-off?**
- Does it introduce breaking changes?
- Does it add complexity vs. value?
- Is it aligned with project goals?

**3. Is it correct for this codebase?**
- Check if it follows patterns in `AGENTS.md`
- Verify against existing code conventions
- Consider project-specific requirements

**Example evaluation:**
```
Comment: "Move DB write from utility to route handler"

Analysis:
✅ AGREE: Separation of concerns (utility does one thing)
✅ AGREE: Consistent with project's request.app.user pattern
⚠️  BREAKS: Changes function signature (acceptable in spec)
✅ DECISION: Accept, it's architecturally superior
```

Document your reasoning and decision before making changes.

### Step 2.3: Get Review Comments (If Needed)

To retrieve specific review comments programmatically:

```bash
# Get all review comments with IDs for replies
gh api repos/OWNER/REPO/pulls/<PR_NUMBER>/comments --jq '.[] | {id: .id, path: .path, line: .line, body: .body}'
```

This is useful when you need comment IDs to reply to specific feedback.

### Step 2.4: Reply to Review Comments

After addressing feedback, document what was done by replying to each comment thread:

**Reply to a specific review comment:**
```bash
# Get comment ID from the PR discussion threads
gh pr view <PR_NUMBER> --comments

# Reply to specific comment
gh api repos/OWNER/REPO/pulls/<PR_NUMBER>/comments/<COMMENT_ID>/replies \
  -X POST \
  -f body="✅ Fixed: Updated authenticate_user() to return (user, new_hash) tuple.
  - Moved DB update to route handler
  - Using request.app.user pattern per project conventions
  - Added proper exception handling (PyMongoError)

  See commit: [sha]"

# CRITICAL: Verify commit succeeded
git log --oneline -3  # Confirm commit appears
git status            # Check for uncommitted changes (pre-commit can fail silently)
```

**Mark conversations as resolved** (after fixing the issues):

```bash
# Step 1: Get review thread IDs
gh api graphql -f query='
query {
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: PR_NUMBER) {
      id
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 1) {
            nodes {
              body
            }
          }
        }
      }
    }
  }
}'

# Step 2: Add a reply comment documenting your fix (RECOMMENDED)
gh api graphql -f query='
mutation {
  addPullRequestReviewThreadReply(input: {
    pullRequestId: "PR_ID_from_step_1"
    threadId: "PRRT_xxxxx"
    body: "✅ Fixed: [Brief description of fix]

- Change 1
- Change 2

See commit: [sha]"
  }) {
    comment {
      id
    }
  }
}'

# Step 3: Resolve each thread by ID
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "PRRT_xxxxx"}) {
    thread {
      id
      isResolved
    }
  }
}'
```

> [!TIP]
> **Best Practice:**
> 1. Run the query to get thread IDs and PR ID (look for `"id": "PRRT_xxxxx"` and `pullRequest.id`)
> 2. **Add a reply comment** to each thread explaining what you fixed and referencing the commit SHA
> 3. Then resolve the thread
> 4. The `isOutdated: true` flag indicates the code has changed since the comment
> 5. After resolving all threads, the PR should be mergeable

### Step 2.5: Request Re-Review (After Addressing Feedback)

After fixing issues identified by `gemini-code-assist`, request a fresh review:

**Option A: GitHub UI (Recommended)**
- Go to PR page → "Reviewers" sidebar → Click ↻ next to `gemini-code-assist`
- This is the native GitHub re-request review feature

**Option B: Command Line with `/gemini review`**
```bash
gh pr comment <PR_NUMBER> --body "/gemini review"
```

**Option C: GitHub CLI re-request** (if gemini-code-assist is a formal reviewer)
```bash
gh pr edit <PR_NUMBER> --add-reviewer gemini-code-assist
```

> [!TIP]
> Option A (UI) is cleanest. The `/gemini review` command also works and explicitly requests a new review.

**Other useful commands:**
- `/gemini summary` - Get updated PR summary
- `@gemini-code-assist <question>` - Ask specific questions

Wait for the new review before proceeding to merge.

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

> [!TIP]
> If CI fails due to missing functionality (not just bugs), consider whether a spec update is needed via `/development-workflow`.

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
gh pr comment <PR_NUMBER> --body "Closing this PR as the issue is now tracked in #<ISSUE_NUMBER>."
gh pr close <PR_NUMBER>
```

## Step 6: Update Documentation

If you encounter new patterns, add them to `AGENTS.md`.
