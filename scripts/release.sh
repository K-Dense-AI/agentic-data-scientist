#!/usr/bin/env bash
# Simple release script - creates a tag and pushes it for GitHub release
# Usage: ./scripts/release.sh <version>
# Example: ./scripts/release.sh 0.2.0

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

error() { echo -e "${RED}Error: $1${NC}" >&2; exit 1; }
info() { echo -e "${BLUE}$1${NC}"; }
success() { echo -e "${GREEN}$1${NC}"; }
warning() { echo -e "${YELLOW}$1${NC}"; }

[ -z "$1" ] && error "Version required. Usage: ./scripts/release.sh <version>"

VERSION=$1
TAG="v$VERSION"

[[ ! $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] && error "Version must be X.Y.Z format"

info "=== Release $VERSION ==="

# Check for uncommitted changes
git diff-index --quiet HEAD -- || error "Uncommitted changes detected"

# Check if tag exists
git rev-parse "$TAG" >/dev/null 2>&1 && error "Tag $TAG already exists"

# Update version in pyproject.toml
info "Updating pyproject.toml..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml
else
    sed -i "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml
fi

# Run tests
info "Running tests..."
uv run pytest tests/unit -v
success "✓ Tests passed"

# Build
info "Building package..."
uv build
success "✓ Build complete"

# Show recent commits
info "Recent commits:"
git log --oneline -10

echo
warning "This will create tag $TAG and push to GitHub."
warning "You can then create a release manually on GitHub."
read -p "Continue? (y/N) " -n 1 -r
echo

[[ ! $REPLY =~ ^[Yy]$ ]] && { warning "Cancelled"; git checkout pyproject.toml; exit 0; }

# Commit and tag
git add pyproject.toml
git commit -m "chore: bump version to $VERSION"
git tag -a "$TAG" -m "Release $VERSION"
git push origin main
git push origin "$TAG"

success "✓ Released $VERSION!"
echo
info "Next: Create release on GitHub at:"
info "https://github.com/K-Dense-AI/agentic-data-scientist/releases/new?tag=$TAG"
