#!/usr/bin/env python3
"""Script to update README.md with test results."""

import datetime
import os
import re


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

    # Generate timestamp
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Create the test results section
    new_section = f"""## Test Results

![Tests](https://github.com/{repo}/actions/workflows/test.yml/badge.svg)

```
{test_output}```

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
