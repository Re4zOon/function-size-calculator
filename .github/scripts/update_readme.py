#!/usr/bin/env python3
"""Script to update README.md with test results."""

import datetime
import os
import re
from collections import defaultdict


def parse_test_output(test_output):
    """Parse pytest output to extract test summary information."""
    # Extract platform information - note: pytest version has a hyphen (pytest-X.Y.Z)
    platform_match = re.search(r'platform (\S+) -- Python ([\d.]+), pytest-([\d.]+)', test_output)
    platform = platform_match.group(1) if platform_match else "linux"
    python_version = platform_match.group(2) if platform_match else "3.12.0"
    pytest_version = platform_match.group(3) if platform_match else "9.0.0"
    
    # Extract execution time
    time_match = re.search(r'(\d+) passed in ([\d.]+)s', test_output)
    total_passed = int(time_match.group(1)) if time_match else 0
    exec_time = time_match.group(2) if time_match else "0"
    
    # Extract test categories and counts
    test_categories = defaultdict(int)
    test_pattern = r'tests/test_\w+\.py::(\w+)::\w+ PASSED'
    
    for match in re.finditer(test_pattern, test_output):
        category = match.group(1)
        test_categories[category] += 1
    
    return {
        'platform': platform,
        'python_version': python_version,
        'pytest_version': pytest_version,
        'total_passed': total_passed,
        'exec_time': exec_time,
        'categories': test_categories
    }


def format_category_name(category):
    """Convert test class name to readable category name."""
    # Map specific categories to friendly names
    category_map = {
        'TestFunctionInfo': 'FunctionInfo',
        'TestJavaScriptParser': 'JavaScript/TypeScript Parser',
        'TestJavaParser': 'Java Parser',
        'TestExcelWriter': 'Excel Writer',
        'TestJSONWriter': 'JSON Writer',
        'TestScanRepository': 'Repository Scanner',
        'TestCommandLineArguments': 'Command-Line Arguments'
    }
    return category_map.get(category, category)


def generate_test_summary_table(test_info):
    """Generate a markdown table summarizing test results."""
    categories = test_info['categories']
    total_tests = test_info['total_passed']
    
    # Build table rows
    rows = []
    for category, count in sorted(categories.items()):
        friendly_name = format_category_name(category)
        rows.append(f"| **{friendly_name}** | {count} | ✅ All Passed |")
    
    # Add total row
    rows.append(f"| **Total** | **{total_tests}** | **✅ {total_tests} Passed** |")
    
    table = "| Test Category | Tests | Status |\n"
    table += "|--------------|-------|--------|\n"
    table += "\n".join(rows)
    
    return table


def main():
    """Update README.md with test results from test-output.txt."""
    # Check if test output file exists
    if not os.path.exists("test-output.txt"):
        print("Error: test-output.txt not found")
        return 1

    # Get repository name from environment
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("Error: GITHUB_REPOSITORY environment variable is not set")
        return 1

    # Read test output
    with open("test-output.txt", "r", encoding="utf-8") as f:
        test_output = f.read()

    # Read current README
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Parse test output
    test_info = parse_test_output(test_output)
    
    # Generate timestamp
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Generate test summary table
    summary_table = generate_test_summary_table(test_info)
    
    # Create the test results section with table format
    new_section = f"""## Test Results

![Tests](https://github.com/{repo}/actions/workflows/test.yml/badge.svg)

### Test Summary

{summary_table}

### Performance

- **Execution Time**: {test_info['exec_time']} seconds
- **Platform**: {test_info['platform'].title()}, Python {test_info['python_version']}, pytest {test_info['pytest_version']}

*Last updated: {timestamp}*"""

    # Check if the test results section already exists
    if "## Test Results" in content:
        # Replace existing test results section (everything from ## Test Results to the next ## or end)
        pattern = r"## Test Results.*?(?=\n## |\Z)"
        content = re.sub(pattern, new_section, content, flags=re.DOTALL)
    else:
        # Insert before ## License if it exists, otherwise at the end
        if "## License" in content:
            content = content.replace("## License", new_section + "\n\n## License")
        else:
            content = content.rstrip() + "\n\n" + new_section + "\n"

    # Write updated README
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print("README.md updated with test results.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
