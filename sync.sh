#!/bin/bash

# Direct URLs as requested
FORK_URL="https://github.com/urdead12/perplexity-openai-api-updated"
SOURCE_URL="https://github.com/henrique-coder/perplexity-webui-scraper"
UPSTREAM="original_source"
BRANCH="main"

set -e # Exit if any command fails

echo "--- Syncing your fork with the original source ---"

# 1. Add the primary source as a remote if it doesn't exist
if ! git remote | grep -q "^$UPSTREAM$"; then
    echo "Adding remote: $UPSTREAM -> $SOURCE_URL"
    git remote add "$UPSTREAM" "$SOURCE_URL"
else
    echo "Remote '$UPSTREAM' already exists. Updating URL..."
    git remote set-url "$UPSTREAM" "$SOURCE_URL"
fi

# 2. Fetch the absolute latest code from the primary source
echo "Fetching updates from $SOURCE_URL..."
git fetch "$UPSTREAM"

# 3. Ensure you are on the correct branch
echo "Switching to branch: $BRANCH"
git checkout "$BRANCH"

# 4. Merge the source's main branch into your fork's main branch
echo "Merging $UPSTREAM/$BRANCH into local $BRANCH..."
if git merge "$UPSTREAM/$BRANCH" --no-edit; then
    # 5. Push the changes to your fork on GitHub
    echo "Pushing synced code to your fork: $FORK_URL"
    git push origin "$BRANCH"
    echo "--- SYNC COMPLETE ---"
else
    echo "ERROR: Merge conflicts detected. Please resolve them manually."
    exit 1
fi
