# Distribution

## PyPI

Cutesy is distributed via PyPI with pre-built wheels for all major platforms.

### For Users

Install from PyPI:
```bash
pip install cutesy
```

Users automatically get pre-compiled mypyc extensions (3-5x faster) for their platform.

### For Maintainers

**Automated Publishing:**

Publishing happens automatically via GitHub Actions when you push a tag:

```bash
git tag v1.0b12
git push origin v1.0b12
```

This triggers `.github/workflows/publish-to-pypi.yml` which:
1. Builds wheels for all platforms (Linux, macOS, Windows)
2. Builds wheels for all Python versions (3.11, 3.12, 3.13)
3. Builds source distribution
4. Publishes to PyPI using trusted publishing

**Platforms Supported:**
- Linux: x86_64
- macOS: x86_64 (Intel), arm64 (Apple Silicon)
- Windows: x64

All wheels include mypyc-compiled extensions for 3-5x performance boost.

**Manual Build (for testing):**

```bash
# Build wheel with mypyc
make build release=true

# Output will be in dist/
ls dist/
```

## Homebrew

The Homebrew formula is in `homebrew/cutesy.rb`.

### Local Testing

```bash
# Install from local formula
brew install --build-from-source ./homebrew/cutesy.rb

# Test
cutesy --version
```

### Updating the Formula

When releasing a new version:

1. Update version in `homebrew/cutesy.rb`
2. Update SHA256 checksums:
   ```bash
   # Download release tarball
   curl -L https://github.com/chasefinch/cutesy/archive/refs/tags/v1.0b12.tar.gz -o cutesy.tar.gz

   # Get SHA256
   shasum -a 256 cutesy.tar.gz
   ```
3. Update resource URLs and checksums for dependencies

### Publishing to homebrew-core

To add Cutesy to the official Homebrew repository, submit a PR to:
https://github.com/Homebrew/homebrew-core

See: https://docs.brew.sh/Adding-Software-to-Homebrew

## Other Package Managers

### pipx (Isolated Installation)

```bash
pipx install cutesy
```

Installs Cutesy in an isolated environment as a CLI tool.

### GitHub Releases

Each release tag automatically creates a GitHub Release with:
- Source code archives (.tar.gz, .zip)
- Release notes

Wheels are hosted on PyPI, not GitHub Releases.
