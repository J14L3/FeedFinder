#!/usr/bin/env python3
"""
Dependency Checker for FeedFinder Backend
Checks if all required dependencies are installed and optionally checks for updates/security issues.
"""

import sys
import subprocess
from pathlib import Path

# Use importlib.metadata (Python 3.8+) instead of deprecated pkg_resources
try:
    from importlib.metadata import distributions, version, PackageNotFoundError
except ImportError:
    # Fallback for Python 3.7 and below (though not recommended)
    try:
        from importlib_metadata import distributions, version, PackageNotFoundError
    except ImportError:
        print("❌ Error: importlib.metadata not available. Please use Python 3.8 or higher.")
        sys.exit(1)

def read_requirements():
    """Read requirements.txt and return list of required packages."""
    requirements_file = Path(__file__).parent / 'requirements.txt'
    if not requirements_file.exists():
        print(f"❌ Error: {requirements_file} not found!")
        return []
    
    requirements = []
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                # Handle version specifiers (e.g., "Flask==3.1.2" or "Flask>=3.0.0")
                if '==' in line:
                    package_name = line.split('==')[0].strip()
                    version = line.split('==')[1].strip()
                    requirements.append((package_name, version))
                elif '>=' in line or '<=' in line or '>' in line or '<' in line:
                    # For ranges, just get the package name
                    package_name = line.split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
                    requirements.append((package_name, None))
                else:
                    requirements.append((line, None))
    
    return requirements

def check_installed_packages():
    """Check if all required packages are installed."""
    requirements = read_requirements()
    if not requirements:
        return False
    
    missing_packages = []
    wrong_version = []
    
    # Build a dictionary of installed packages using importlib.metadata
    installed_packages = {}
    try:
        for dist in distributions():
            # Normalize package name to lowercase for comparison
            # Some packages have different naming conventions (e.g., Flask vs flask)
            dist_name = dist.name
            if dist_name:
                installed_packages[dist_name.lower()] = dist.version
    except Exception as e:
        print(f"⚠️  Error reading installed packages: {e}")
        # Fallback: try to get packages individually
        installed_packages = {}
    
    print("🔍 Checking Python dependencies...\n")
    
    for package_name, required_version in requirements:
        package_key = package_name.lower()
        
        # Try to get version using importlib.metadata.version as fallback
        installed_version = None
        if package_key in installed_packages:
            installed_version = installed_packages[package_key]
        else:
            # Try direct lookup (case-insensitive)
            try:
                installed_version = version(package_name)
                installed_packages[package_key] = installed_version
            except PackageNotFoundError:
                pass
        
        if installed_version is None:
            missing_packages.append(package_name)
            print(f"❌ {package_name} - NOT INSTALLED")
        else:
            if required_version:
                if installed_version != required_version:
                    wrong_version.append((package_name, required_version, installed_version))
                    print(f"⚠️  {package_name} - Version mismatch (required: {required_version}, installed: {installed_version})")
                else:
                    print(f"✅ {package_name} - {installed_version}")
            else:
                print(f"✅ {package_name} - {installed_version}")
    
    print("\n" + "="*60)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("\nTo install missing packages, run:")
        print("  pip install -r requirements.txt")
        return False
    
    if wrong_version:
        print(f"\n⚠️  Version mismatches found: {len(wrong_version)}")
        print("\nTo fix version mismatches, run:")
        print("  pip install -r requirements.txt --upgrade")
        return False
    
    print("\n✅ All dependencies are installed correctly!")
    return True

def check_outdated_packages():
    """Check for outdated packages using pip list --outdated."""
    print("\n🔍 Checking for outdated packages...\n")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--outdated'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 2:  # Header + separator + packages
                outdated = lines[2:]
                if outdated:
                    print("⚠️  Outdated packages found:")
                    for line in outdated:
                        print(f"   {line}")
                    print("\nTo update packages, run:")
                    print("  pip install --upgrade <package-name>")
                    return False
                else:
                    print("✅ All packages are up to date!")
                    return True
            else:
                print("✅ All packages are up to date!")
                return True
        else:
            print("⚠️  Could not check for outdated packages")
            return True
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout while checking for outdated packages")
        return True
    except Exception as e:
        print(f"⚠️  Error checking outdated packages: {e}")
        return True

def check_security_vulnerabilities():
    """Check for known security vulnerabilities using pip-audit or safety."""
    print("\n🔍 Checking for security vulnerabilities...\n")
    
    # Try pip-audit first (recommended)
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip_audit', '--requirement', 'requirements.txt'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            if 'No known vulnerabilities found' in result.stdout or 'No known vulnerabilities' in result.stdout:
                print("✅ No known security vulnerabilities found!")
                return True
            else:
                print("⚠️  Security vulnerabilities found:")
                print(result.stdout)
                print("\nTo fix vulnerabilities, update affected packages:")
                print("  pip install --upgrade <package-name>")
                return False
        else:
            # pip-audit not installed or error
            print("ℹ️  pip-audit not available. Install it with: pip install pip-audit")
            print("   Or use safety: pip install safety")
            return True
    except FileNotFoundError:
        # Try safety as fallback
        try:
            result = subprocess.run(
                ['safety', 'check', '--file', 'requirements.txt'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ No known security vulnerabilities found!")
                return True
            else:
                print("⚠️  Security vulnerabilities found:")
                print(result.stdout)
                return False
        except FileNotFoundError:
            print("ℹ️  Security check tools not installed.")
            print("   Install pip-audit: pip install pip-audit")
            print("   Or install safety: pip install safety")
            return True
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout while checking security vulnerabilities")
        return True
    except Exception as e:
        print(f"⚠️  Error checking security: {e}")
        return True

def main():
    """Main function to run all dependency checks."""
    print("="*60)
    print("FeedFinder Backend - Dependency Checker")
    print("="*60)
    
    # Check if all packages are installed
    all_installed = check_installed_packages()
    
    if not all_installed:
        print("\n❌ Dependency check failed! Please install missing packages.")
        sys.exit(1)
    
    # Optional checks (won't fail the script)
    check_outdated_packages()
    check_security_vulnerabilities()
    
    print("\n" + "="*60)
    print("✅ Dependency check completed!")
    print("="*60)
    sys.exit(0)

if __name__ == '__main__':
    main()

