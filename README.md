# Function Size Calculator

A Python tool that scans git repositories to find the largest functions in Java and Node.js codebases. The results are exported to an Excel (XLS) file with each repository on a separate tab.

## Features

- Scans multiple git repositories (local or remote)
- Supports Node.js (JavaScript, TypeScript) and Java
- Finds the 5 largest functions in each repository
- Exports results to Excel format with:
  - Each repository on a separate tab
  - Function name, file path, line numbers, and size
  - Formatted headers and auto-sized columns

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Re4zOon/function-size-calculator.git
cd function-size-calculator
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.6 or higher
- Git (for cloning remote repositories)
- openpyxl (automatically installed from requirements.txt)

## Usage

### Basic Usage

Scan one or more repositories:

```bash
python function_size_calculator.py <repository-path-or-url> [<repository-path-or-url> ...]
```

### Examples

1. Scan a remote repository:
```bash
python function_size_calculator.py https://github.com/user/repo.git
```

2. Scan multiple repositories:
```bash
python function_size_calculator.py https://github.com/user/repo1.git https://github.com/user/repo2.git
```

3. Scan local repositories:
```bash
python function_size_calculator.py /path/to/local/repo1 /path/to/local/repo2
```

4. Specify custom output file:
```bash
python function_size_calculator.py -o my_results.xlsx https://github.com/user/repo.git
```

5. Mix local and remote repositories:
```bash
python function_size_calculator.py /local/repo https://github.com/user/remote-repo.git
```

### Command-Line Options

- `repositories`: One or more git repository URLs or local paths (required)
- `-o`, `--output`: Output Excel file name (default: `function_sizes.xlsx`)
- `-h`, `--help`: Show help message

## Output Format

The tool generates an Excel file with the following structure:

- **Each repository gets its own tab** named after the repository
- **Columns in each tab:**
  - Rank: Position in top 5 (1-5)
  - Function Name: Name of the function/method
  - File Path: Relative path to the file containing the function
  - Start Line: Line number where the function starts
  - End Line: Line number where the function ends
  - Lines of Code: Total lines in the function

## Supported Languages

### Node.js / JavaScript / TypeScript
- Function declarations: `function name() {}`
- Arrow functions: `const name = () => {}`
- Methods: `name() {}`
- Class methods: `async name() {}`
- Supports: `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs` files

### Java
- Methods with various modifiers: `public static void method() {}`
- Supports: `.java` files

## How It Works

1. **Repository Access**: Clones remote repositories to a temporary directory or uses local paths
2. **File Discovery**: Recursively finds all relevant source files (skips `node_modules`, `.git`, `target`, etc.)
3. **Function Parsing**: Uses regex patterns to identify function/method declarations
4. **Size Calculation**: Counts lines by tracking brace pairs `{}`
5. **Ranking**: Sorts functions by line count and selects top 5 per repository
6. **Export**: Creates formatted Excel file with results
7. **Cleanup**: Removes temporary cloned repositories

## Limitations

- Function size is measured by line count (including braces and blank lines)
- Nested functions are counted separately
- Very complex or unconventional syntax may not be detected
- Excludes common dependency directories (node_modules, target, build, etc.)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
