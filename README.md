# rav

A cross-platform Python CLI to shortcut to command-line commands with powerful file download capabilities and integrity verification. Inspired by Makefiles and npm scripts.

## Features

✨ **Script Management**: Define and run custom command shortcuts  
📦 **File Downloads**: Download files with integrity verification  
🔒 **Security**: Subresource Integrity (SRI) hash verification  
🎨 **Rich Output**: Beautiful terminal output with progress indicators  
⚡ **Multiple Formats**: Support for single commands and multi-command sequences  
🔧 **Flexible Config**: Use `rav`, `scripts`, or `commands` as top-level keys  

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start)
- [CLI Commands Reference](#cli-commands-reference)
- [Script Configuration](#script-configuration)
- [File Downloads](#file-downloads)
- [Integrity Verification](#integrity-verification)
- [Complete Examples](#complete-examples)
- [Tips and Best Practices](#tips-and-best-practices)

## Install

It's recommended that you use a virtual environment with `rav`. 

```bash
python3 -m pip install rav
```
> Minimum python version is 3.7

## Quick Start

### Option 1: Interactive Setup

```bash
cd ~/path/to/project
rav new
```
> Run through the setup wizard to create `rav.yaml`

### Option 2: Manual Setup

Create `rav.yaml`:

```yaml
scripts:
    echo: echo hello world
    server: python -m http.server 8000
```

Run commands:

```bash
rav run echo     # or rav x echo
rav run server   # Start development server  
rav list         # Show all available commands
```

## CLI Commands Reference

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `rav run <command>` | Execute a script command | `rav run server` |
| `rav x <command>` | Shortcut for `rav run` | `rav x echo` |
| `rav list` | List all available commands | `rav list` |
| `rav new` | Create new rav project with wizard | `rav new` |
| `rav sample` | Generate sample rav.yaml file | `rav sample` |
| `rav version` | Show rav version | `rav version` |

### Download Commands

| Command | Description | Example |
|---------|-------------|---------|
| `rav download <config>` | Download files using config | `rav download staticfiles` |
| `rav downloads <config>` | Alias for `rav download` | `rav downloads staticfiles` |

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `-f, --file` | Use custom rav file | `rav run -f custom.yaml echo` |
| `--overwrite` | Force overwrite existing files | `rav sample --overwrite` |
| `--verbose` | Enable verbose output | `rav --verbose run command` |

### Quick Examples

**Script execution:**
```bash
rav x server          # Start development server
rav x test            # Run tests  
rav x build           # Build project
```

**Custom files:**
```bash
rav run -f project.yaml deploy
rav list -f staging.yaml
```

**Project management:**
```bash
rav new              # Interactive project setup
rav sample           # Create example file
rav list             # View available commands
```

## Script Configuration

The configuration block is flexible. Use `rav`, `scripts`, or `commands` as the top-level key.

`rav.yaml`
```yaml
name: web-development-toolkit

scripts:
    # Development servers
    dev: python -m http.server 8000
    dev-secure: python -m http.server 8443 --bind 127.0.0.1
    
    # Testing and quality assurance  
    test: pytest tests/ -v
    lint: flake8 src/ tests/
    format: black src/ tests/
    
    # Build and deployment
    build:
        - npm run build
        - python setup.py sdist bdist_wheel
        - echo "Build complete!"
    
    deploy:
        - rav run test
        - rav run build  
        - rsync -av dist/ user@server:/var/www/

downloads:
    frontend-deps:
        destination: static/vendor
        overwrite: true
        files:
            - name: htmx.min.js
              url: https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js
              integrity: sha384-Akqfrbj/HpNVo8k11SXBb6TlBWmXXlYQrCSqEWmyKJe+hDm3Z/B2WVG4smwBkRVm
            - name: tailwind.css
              url: https://cdn.tailwindcss.com/3.4.0/tailwind.min.css
```

### Flexible Configuration Keys

The following all work and will run in this exact order (`rav` first, `scripts` second, `commands` last):

```yaml
rav:
    echo: echo "this is awesome"
    server: venv/bin/python -m http.server
```

```yaml
scripts:
    echo: echo "this is awesome"  
    server: venv/bin/python -m http.server
```

```yaml
commands:
    echo: echo "this is awesome"
    server: venv/bin/python -m http.server
```



### Basic Syntax

Commands follow this simple pattern:

```bash
rav run <command>       # Execute a script command
rav x <command>         # Shortcut for rav run
rav list                # Show all available commands
```

### Sample Project

Generate a sample project to explore features:

```bash
rav sample              # Creates rav.sample.yaml
rav run -f rav.sample.yaml echo
```

## Custom Rav File
Rav supports custom yaml files by default. The yaml declaration needs to be any of the following:

- `rav`
- `scripts`
- `commands`

`project.yaml`
```yaml
rav:
    sweet: echo "this is working"
    echo: echo "so is this"
```

`rav.basic.yaml`
```yaml
scripts:
    sweet: echo "this is working"
    echo: echo "so is this"
```

```
rav run -f project.yaml sweet
```
or
```
rav run --file rav.other.yaml echo
```

Here's a few rules for custom files:

- `-f` or `--file` is used to specify a custom rav file
- `-f` or `--file` must be used prior to the command shortcut name (e.g. `rav run -f <your-new-file> <your-command>`)


## Multiple Commands at Once

`rav.yaml`
```yaml
scripts:
    multi: 
        - echo this is
        - echo awesome
        - echo simple
        - echo and 
        - echo easy
```

Run with:

```
rav run multi
```

This is the same as running:

```
echo this is && echo awesome && echo simple && echo and && echo easy
```

## File Downloads

Rav includes powerful file download capabilities with support for integrity verification, custom destinations, and batch downloads.

### Basic Download Configuration

Add a `downloads` section to your `rav.yaml`:

```yaml
name: my-project

scripts:
    serve: python -m http.server

downloads:
    assets:
        destination: static/vendor
        files:
            - name: htmx.min.js
              url: https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js
            - name: tailwind.css
              url: https://cdn.tailwindcss.com/3.4.0/tailwind.min.css
```

### Download Commands

```bash
rav download assets     # Download all files in 'assets' config
rav downloads assets    # Same as above (alias)
```

### Advanced Download Configuration

```yaml
downloads:
    frontend-deps:
        name: Frontend Dependencies
        destination: static/vendor
        verbose: true                    # Show detailed progress
        overwrite: true                  # Overwrite existing files
        raise_on_error: false           # Continue on individual file errors
        files:
            - name: htmx.min.js
              url: https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js
              integrity: sha384-Akqfrbj/HpNVo8k11SXBb6TlBWmXXlYQrCSqEWmyKJe+hDm3Z/B2WVG4smwBkRVm
              destination: static/js     # Override global destination
              overwrite: false           # Override global overwrite setting
            
            - name: bootstrap.min.css
              url: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
              destination: static/css
```

### Configuration Options

| Option | Level | Description | Default |
|--------|-------|-------------|---------|
| `name` | Download | Human-readable name for the download set | - |
| `destination` | Download/File | Where to save files | Required |
| `verbose` | Download | Show detailed download progress | `true` |
| `overwrite` | Download/File | Overwrite existing files | `false` |
| `raise_on_error` | Download | Stop on any download error | `false` |
| `integrity` | File | SRI hash for verification | - |
| `url` | File | Download URL | Required |
| `name` or `filename` | File | Local filename | URL basename |

### File-Level Overrides

Individual files can override the download-level settings:

```yaml
downloads:
    mixed-settings:
        destination: assets/
        overwrite: false
        verbose: true
        files:
            - name: important-file.js
              url: https://example.com/file.js
              overwrite: true          # Override: will overwrite
              destination: critical/   # Override: different folder
            
            - name: optional-file.css
              url: https://example.com/style.css
              # Uses download-level settings
```

### Download Output

Rav provides rich, colored output showing download progress:

```
📥 Starting download: frontend-deps
Destination: static/vendor
Files to download: 3
Overwrite existing: true

[1/3] ⬇️  Downloading: htmx.min.js
   → From: https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js
   → Integrity: sha384-Akqfrbj/...
   ✅ Integrity verified (sha384)
   ✅ Success! (45,234 bytes)

[2/3] ⏭️  Skipping existing file: bootstrap.min.css

[3/3] ⬇️  Downloading: alpine.min.js
   ✅ Success! (15,678 bytes)

---------------------------------------
📊 Download Summary:
   ✅ Downloaded: 2 files
   ⏭️  Skipped: 1 files
---------------------------------------
```

## Integrity Verification

Rav supports Subresource Integrity (SRI) verification to ensure downloaded files haven't been tampered with.

### What is SRI?

Subresource Integrity is a security feature that allows you to verify that downloaded files haven't been modified. It uses cryptographic hashes (SHA256, SHA384, SHA512) to ensure file integrity.

### Supported Hash Algorithms

- **SHA256**: `sha256-<base64hash>`
- **SHA384**: `sha384-<base64hash>` 
- **SHA512**: `sha512-<base64hash>`

### Getting SRI Hashes

You can generate SRI hashes using online tools or command line:

**Online Tools:**
- [SRI Hash Generator](https://www.srihash.org/)
- [KeyCDN SRI Hash Generator](https://tools.keycdn.com/sri)

**Command Line:**
```bash
# SHA384 (recommended)
curl -s https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js | \
  openssl dgst -sha384 -binary | openssl base64 -A

# SHA256
curl -s https://example.com/file.js | \
  openssl dgst -sha256 -binary | openssl base64 -A
```

### Using Integrity Verification

Add the `integrity` field to any file in your download configuration:

```yaml
downloads:
    secure-assets:
        destination: static/vendor
        files:
            - name: htmx.min.js
              url: https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js
              integrity: sha384-Akqfrbj/HpNVo8k11SXBb6TlBWmXXlYQrCSqEWmyKJe+hDm3Z/B2WVG4smwBkRVm
            
            - name: bootstrap.min.css
              url: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
              integrity: sha384-9ndCyUa/9zzCGWL/iDMdwc9/z3dNS0MaTp5XhVpw5gGa6NZJK5YF6vZmN3K5J5zF
```

### Integrity Verification Process

When integrity is specified, rav will:

1. Download the file to a temporary location
2. Calculate the file's hash using the specified algorithm
3. Compare against the expected hash
4. Move file to final destination only if verification passes
5. Delete file and report error if verification fails

### Error Handling

**With `raise_on_error: false` (default):**
- Failed verification logs an error and continues
- Failed files are not saved to destination
- Download summary shows verification failures

**With `raise_on_error: true`:**
- Failed verification stops the entire download process
- Throws an exception with detailed error information

### Example Output with Integrity

```
[1/2] ⬇️  Downloading: htmx.min.js
   → From: https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js
   → Integrity: sha384-Akqfrbj/...
   → Downloading to temp for verification: /tmp/rav_downloads/htmx.min.js
   ✅ Integrity verified (sha384)
   → Downloaded to final destination: static/vendor/htmx.min.js
   ✅ Success! (45,234 bytes)

[2/2] ⬇️  Downloading: compromised-file.js
   → From: https://example.com/file.js
   → Integrity: sha384-Expected123...
   ❌ Integrity check failed: sha384-Actual456... != sha384-Expected123...
```

### Security Best Practices

1. **Always use integrity hashes for CDN files**
2. **Use SHA384 or SHA512** for better security than SHA256
3. **Verify hashes from trusted sources** (official documentation, package registries)
4. **Set `raise_on_error: true`** for critical security files
5. **Keep hashes updated** when updating file versions

## Complete Examples

### Web Development Project

A complete `rav.yaml` for a modern web development workflow:

```yaml
name: my-web-app

scripts:
    # Development
    dev: python -m http.server 8000
    dev-watch: 
        - npm run watch
        - rav run dev
    
    # Code quality
    lint:
        - flake8 src/
        - npm run lint
        - echo "✅ Linting complete"
    
    format:
        - black src/
        - prettier --write static/js/
    
    test:
        - pytest tests/ -v --cov=src
        - npm test
    
    # Build pipeline
    build:
        - rm -rf dist/
        - rav download frontend-deps
        - npm run build
        - python setup.py sdist bdist_wheel
        - echo "🚀 Build complete!"
    
    # Deployment
    deploy-staging:
        - rav run test
        - rav run build
        - rsync -av dist/ staging@server:/var/www/staging/
    
    deploy-prod:
        - rav run test
        - rav run build
        - rsync -av dist/ prod@server:/var/www/production/

downloads:
    frontend-deps:
        name: Frontend Dependencies
        destination: static/vendor
        verbose: true
        overwrite: true
        files:
            # CSS Frameworks
            - name: bootstrap.min.css
              url: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
              integrity: sha384-9ndCyUa/9zzCGWL/iDMdwc9/z3dNS0MaTp5XhVpw5gGa6NZJK5YF6vZmN3K5J5zF
              destination: static/css
            
            # JavaScript Libraries
            - name: htmx.min.js
              url: https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js
              integrity: sha384-Akqfrbj/HpNVo8k11SXBb6TlBWmXXlYQrCSqEWmyKJe+hDm3Z/B2WVG4smwBkRVm
              destination: static/js
            
            - name: alpine.min.js
              url: https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js
              destination: static/js
```

### Data Science Project

Perfect for Jupyter notebooks and data analysis:

```yaml
name: data-analysis-project

scripts:
    # Environment management
    setup:
        - python -m venv venv
        - venv/bin/pip install -r requirements.txt
        - echo "✅ Environment ready!"
    
    # Jupyter workflows
    notebook: venv/bin/jupyter lab --port=8888
    notebook-clean: venv/bin/jupyter nbconvert --clear-output notebooks/*.ipynb
    
    # Data processing
    download-data: python scripts/download_datasets.py
    process: 
        - python scripts/clean_data.py
        - python scripts/feature_engineering.py
        - echo "📊 Data processing complete"
    
    # Analysis and reporting
    analyze: venv/bin/python scripts/analyze.py
    report: 
        - venv/bin/jupyter nbconvert --to html notebooks/analysis.ipynb
        - echo "📑 Report generated: notebooks/analysis.html"
    
    # Model training
    train:
        - rav run process
        - python scripts/train_model.py
        - echo "🤖 Model training complete"

downloads:
    datasets:
        destination: data/raw
        files:
            - name: sample_data.csv
              url: https://example.com/datasets/sample.csv
            - name: reference_data.json
              url: https://api.example.com/reference/data.json
```

### DevOps/Infrastructure Project

For managing deployments and infrastructure:

```yaml
name: infrastructure-toolkit

scripts:
    # Infrastructure
    plan: terraform plan
    apply: terraform apply -auto-approve
    destroy: terraform destroy -auto-approve
    
    # Docker workflows
    build: docker build -t myapp:latest .
    run: docker run -p 8080:8080 myapp:latest
    push: 
        - docker tag myapp:latest registry.com/myapp:latest
        - docker push registry.com/myapp:latest
    
    # Kubernetes
    deploy:
        - kubectl apply -f k8s/
        - kubectl rollout status deployment/myapp
    
    logs: kubectl logs -f deployment/myapp
    status: kubectl get pods,services,deployments
    
    # Monitoring setup
    setup-monitoring:
        - rav download monitoring-stack
        - kubectl apply -f monitoring/
        - echo "📊 Monitoring stack deployed"

downloads:
    monitoring-stack:
        destination: monitoring
        files:
            - name: prometheus.yaml
              url: https://raw.githubusercontent.com/prometheus/prometheus/main/documentation/examples/prometheus.yml
            - name: grafana-dashboard.json
              url: https://grafana.com/api/dashboards/1860/revisions/latest/download
```

## Tips and Best Practices

### Script Organization
- **Group related commands** using descriptive names
- **Use comments** in YAML to document complex workflows
- **Chain commands** with `rav run` for reusable components
- **Keep scripts simple** - complex logic belongs in separate files

### File Downloads
- **Always use integrity hashes** for security
- **Organize by purpose** (frontend-deps, datasets, configs)
- **Use descriptive destination paths** for better organization
- **Set appropriate overwrite policies** per use case

### Project Structure
```
my-project/
├── rav.yaml              # Main configuration
├── rav.dev.yaml          # Development-specific config
├── rav.prod.yaml         # Production-specific config
├── scripts/              # Complex automation scripts
├── static/vendor/        # Downloaded dependencies
└── data/raw/            # Downloaded datasets
```

### Cross-Platform Compatibility
```yaml
scripts:
    # Universal commands (recommended)
    test: python -m pytest tests/
    serve: python -m http.server 8000
    
    # Platform-specific alternatives
    serve-win: python -m http.server 8000
    serve-unix: python3 -m http.server 8000
```
