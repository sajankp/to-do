# Branch Protection Configuration

This document provides step-by-step instructions for configuring GitHub branch protection rules.

## Why Branch Protection?

Branch protection prevents:
- Direct pushes to `main` that bypass code review
- Merging PRs that fail CI checks
- Force pushes that rewrite history
- Accidental deletions of protected branches

## Recommended Settings

### For the `main` Branch

Navigate to: **Settings → Branches → Add branch protection rule**

#### Rule Name
Enter: `main`

#### Protection Settings (Recommended)

| Setting | Value | Reason |
|---------|-------|--------|
| **Require a pull request before merging** | ✅ Enabled | Forces code review |
| └─ Required approving reviews | 1 | At least one reviewer |
| └─ Dismiss stale reviews | ✅ | Reset approvals on new commits |
| └─ Require review from CODEOWNERS | ✅ | Uses `.github/CODEOWNERS` |
| **Require status checks to pass** | ✅ Enabled | CI must pass |
| └─ Require branches to be up to date | ✅ | Ensures tested on latest main |
| └─ Status checks: `test` | ✅ Required | Our CI job name |
| **Require conversation resolution** | ✅ | All comments must be resolved |
| **Require linear history** | ✅ | Clean git history |
| **Do not allow bypassing settings** | ✅ | Even admins follow rules |
| **Restrict who can push** | Optional | Leave empty for now |
| **Allow force pushes** | ❌ Disabled | Never allow |
| **Allow deletions** | ❌ Disabled | Protect from accidents |

## Step-by-Step Setup

### 1. Access Branch Protection Settings

1. Go to your repository on GitHub
2. Click **Settings** (gear icon)
3. In the left sidebar, click **Branches**
4. Under "Branch protection rules", click **Add rule**

### 2. Configure the Rule

1. **Branch name pattern**: Enter `main`

2. Enable these checkboxes:
   - [x] Require a pull request before merging
     - [x] Require approvals (set to 1)
     - [x] Dismiss stale pull request approvals when new commits are pushed
   - [x] Require status checks to pass before merging
     - [x] Require branches to be up to date before merging
     - Search and add: `test`
   - [x] Require conversation resolution before merging
   - [x] Do not allow bypassing the above settings

3. Click **Create** or **Save changes**

### 3. Verify CODEOWNERS

The `.github/CODEOWNERS` file is already created. GitHub will automatically:
- Request reviews from specified owners
- Show a badge when all required reviewers approved

## For Solo Developers

If you're the only contributor, you may want to:
- Keep "Require a pull request" enabled (good practice)
- Set required approvals to 0 (you can self-merge)
- Keep "Require status checks" enabled (ensures tests pass)

## Troubleshooting

### "Required status check is expected"
- Ensure the CI workflow has run at least once
- Check that the job name matches exactly (`test`)

### "CODEOWNERS file not found"
- Ensure `.github/CODEOWNERS` is committed to `main`
- Check file permissions and syntax

### "Cannot merge: branch protection rules not satisfied"
- All status checks must pass
- Required reviews must be obtained
- Branch must be up to date with main

## Related Files

- [`.github/CODEOWNERS`](../.github/CODEOWNERS) - Automatic reviewer assignment
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) - CI pipeline
- [`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) - PR template
