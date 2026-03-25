# ============================================================
# push_to_github.ps1
# Pushes this project to a new GitHub repository using only
# the GitHub REST API — no Git installation required.
#
# Usage (open a NEW PowerShell window):
#   cd "C:\Users\sakakkar\old"
#   .\push_to_github.ps1
# ============================================================

param(
    [string]$GitHubUser   = "",
    [string]$GitHubToken  = "",
    [string]$RepoName     = "cinebot-agentic-commerce",
    [string]$BranchName   = "main",
    [bool]$Private        = $false
)

# ── Prompt for missing credentials ──────────────────────────────────────────
if (-not $GitHubUser) {
    $GitHubUser = Read-Host "GitHub username"
}
if (-not $GitHubToken) {
    $rawToken = Read-Host "GitHub Personal Access Token (needs 'repo' scope)" -AsSecureString
    $GitHubToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($rawToken)
    )
}

$headers = @{
    Authorization = "token $GitHubToken"
    Accept        = "application/vnd.github.v3+json"
    "User-Agent"  = "PowerShell-GitHub-Pusher"
}

# ── Helper: GitHub API call ──────────────────────────────────────────────────
function Invoke-GH {
    param([string]$Method, [string]$Url, [hashtable]$Body = $null)
    $params = @{ Method = $Method; Uri = $Url; Headers = $headers; ContentType = "application/json" }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 20) }
    try {
        Invoke-RestMethod @params
    } catch {
        $msg = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        Write-Host "  API ERROR $($_.Exception.Response.StatusCode): $($msg.message)" -ForegroundColor Red
        return $null
    }
}

# ── 1. Create repository ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Creating repository '$RepoName' on GitHub ===" -ForegroundColor Cyan
$repo = Invoke-GH -Method POST -Url "https://api.github.com/user/repos" -Body @{
    name        = $RepoName
    description = "CineBot – Agentic movie-booking chatbot (Claude on AWS Bedrock, Hindi movies from March 2026)"
    private     = $Private
    auto_init   = $false
}
if (-not $repo) {
    # Repo might already exist for this user — try to fetch it
    Write-Host "  Trying to use existing repo..." -ForegroundColor Yellow
    $repo = Invoke-GH -Method GET -Url "https://api.github.com/repos/$GitHubUser/$RepoName"
    if (-not $repo) { Write-Host "Cannot access repo. Aborting." -ForegroundColor Red; exit 1 }
}
Write-Host "  Repo URL : $($repo.html_url)" -ForegroundColor Green

# ── 2. Get or create the initial empty tree so we can push against HEAD ───────
$refsResp = Invoke-GH -Method GET -Url "https://api.github.com/repos/$GitHubUser/$RepoName/git/refs/heads/$BranchName"
$parentSha = $null
if ($refsResp -and $refsResp.object) {
    $parentSha = $refsResp.object.sha
    Write-Host "  Existing branch '$BranchName' found (SHA: $parentSha)"
}

# ── 3. Collect project files ─────────────────────────────────────────────────
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Patterns to skip
$skipPatterns = @(
    "\.git",
    "__pycache__",
    "\.pyc$",
    "node_modules",
    "push_to_github\.ps1"   # skip this script itself
)

$filePaths = Get-ChildItem -Path $rootDir -Recurse -File | Where-Object {
    $rel = $_.FullName.Substring($rootDir.Length + 1).Replace("\", "/")
    $skip = $false
    foreach ($p in $skipPatterns) { if ($rel -match $p) { $skip = $true; break } }
    -not $skip
}

Write-Host ""
Write-Host "=== Uploading $($filePaths.Count) files ===" -ForegroundColor Cyan

# ── 4a. If no existing branch: use Contents API to create files one by one ────
#        This is simpler and suffices for a fresh repo.
# ── 4b. If branch exists    : use Git Tree API to create a single commit ──────

if (-not $parentSha) {
    # Fresh repo — upload files one by one using Contents API
    $count = 0
    foreach ($file in $filePaths) {
        $relPath = $file.FullName.Substring($rootDir.Length + 1).Replace("\", "/")
        $count++
        Write-Host "  [$count/$($filePaths.Count)] $relPath" -NoNewline

        $bytes   = [System.IO.File]::ReadAllBytes($file.FullName)
        $b64     = [Convert]::ToBase64String($bytes)

        $url     = "https://api.github.com/repos/$GitHubUser/$RepoName/contents/$relPath"
        $result  = Invoke-GH -Method PUT -Url $url -Body @{
            message = "Initial commit: $relPath"
            content = $b64
            branch  = $BranchName
        }
        if ($result) { Write-Host " ✓" -ForegroundColor Green }
        else         { Write-Host " ✗ (skipped)" -ForegroundColor Yellow }

        Start-Sleep -Milliseconds 150   # avoid secondary rate limit
    }
} else {
    # Existing branch — use Git Data API to make a single commit with all files
    Write-Host "  Building git tree from $($filePaths.Count) blobs..."

    # Create blobs in parallel (batches of 5)
    $treeItems = @()
    $count = 0
    foreach ($file in $filePaths) {
        $relPath = $file.FullName.Substring($rootDir.Length + 1).Replace("\", "/")
        $count++
        Write-Host "  [$count/$($filePaths.Count)] blob: $relPath" -NoNewline

        $bytes  = [System.IO.File]::ReadAllBytes($file.FullName)
        $b64    = [Convert]::ToBase64String($bytes)

        $blob = Invoke-GH -Method POST -Url "https://api.github.com/repos/$GitHubUser/$RepoName/git/blobs" -Body @{
            content  = $b64
            encoding = "base64"
        }
        if ($blob) {
            Write-Host " ✓"
            $treeItems += @{ path = $relPath; mode = "100644"; type = "blob"; sha = $blob.sha }
        } else {
            Write-Host " ✗ skipped"
        }
        Start-Sleep -Milliseconds 100
    }

    # Create tree
    Write-Host "  Creating tree..."
    $tree = Invoke-GH -Method POST -Url "https://api.github.com/repos/$GitHubUser/$RepoName/git/trees" -Body @{
        base_tree = $parentSha
        tree      = $treeItems
    }

    # Create commit
    Write-Host "  Creating commit..."
    $commit = Invoke-GH -Method POST -Url "https://api.github.com/repos/$GitHubUser/$RepoName/git/commits" -Body @{
        message = "Update: CineBot with Hindi movies, payment recommendation, CodeSandbox support"
        tree    = $tree.sha
        parents = @($parentSha)
    }

    # Update branch ref
    Write-Host "  Updating branch ref..."
    Invoke-GH -Method PATCH -Url "https://api.github.com/repos/$GitHubUser/$RepoName/git/refs/heads/$BranchName" -Body @{
        sha   = $commit.sha
        force = $true
    } | Out-Null

    Write-Host "  Commit SHA: $($commit.sha)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Green
Write-Host "Repository : $($repo.html_url)" -ForegroundColor Cyan
Write-Host "Import into CodeSandbox: https://codesandbox.io/s/github/$GitHubUser/$RepoName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick CodeSandbox import link (click or paste in browser):"
Write-Host "  https://codesandbox.io/s/github/$GitHubUser/$RepoName/tree/$BranchName" -ForegroundColor Yellow
