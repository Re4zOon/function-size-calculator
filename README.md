# Function Size Calculator

A Python tool that scans git repositories to find the largest functions in Java and Node.js codebases. The results are exported to an Excel (XLSX) file with each repository on a separate tab.

## Features

- Scans multiple git repositories (local or remote)
- **Parallel processing** for efficient scanning of multiple repositories
- Supports Node.js (JavaScript, TypeScript) and Java
- Finds the 5 largest functions in each repository
- Exports results to Excel format with:
  - Each repository on a separate tab
  - Function name, file path, line numbers, and size
  - Formatted headers and auto-sized columns
- Automatic cleanup of temporary cloned repositories

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

## Testing

The repository includes a comprehensive test suite to ensure code quality and prevent regressions.

### Running Tests

Run all tests:
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Run specific test class:
```bash
python3 -m unittest tests.test_function_size_calculator.TestJavaScriptParser -v
```

Run a specific test:
```bash
python3 -m unittest tests.test_function_size_calculator.TestJavaScriptParser.test_parse_javascript_file
```

### Test Coverage

The test suite includes:
- **Unit tests** for FunctionInfo class
- **Parser tests** for JavaScript/TypeScript and Java parsers
- **Excel writer tests** for output generation
- **Integration tests** for repository scanning
- **CLI tests** for command-line argument parsing

Test fixtures are located in `tests/fixtures/` and include sample JavaScript, TypeScript, and Java files.

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

4. Scan repositories from an input file:
```bash
# Create a file with repository URLs (one per line)
cat > repos.txt << EOF
https://github.com/user/repo1.git
https://github.com/user/repo2.git
/path/to/local/repo3
# Comments are supported
https://github.com/user/repo4.git
EOF

# Scan all repositories from the file
python function_size_calculator.py -i repos.txt
```

5. Specify custom output file:
```bash
python function_size_calculator.py -o my_results.xlsx https://github.com/user/repo.git
```

6. Mix input file and command-line repositories:
```bash
python function_size_calculator.py -i repos.txt https://github.com/user/extra-repo.git
```

7. Adjust parallel processing (default is 4 parallel jobs):
```bash
python function_size_calculator.py -i repos.txt -j 8  # Use 8 parallel jobs
```

### Command-Line Options

- `repositories`: One or more git repository URLs or local paths (optional if using -i)
- `-i`, `--input-file`: File containing list of repository URLs/paths (one per line, comments with # are supported)
- `-o`, `--output`: Output Excel file name (default: `function_sizes.xlsx`)
- `-j`, `--jobs`: Number of parallel jobs for scanning repositories (default: 4)
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

1. **Repository Access**: Clones remote repositories to temporary directories or uses local paths
2. **Parallel Processing**: Scans multiple repositories concurrently for improved performance
3. **File Discovery**: Recursively finds all relevant source files (skips `node_modules`, `.git`, `target`, etc.)
4. **Function Parsing**: Uses regex patterns to identify function/method declarations
5. **Size Calculation**: Counts lines by tracking brace pairs `{}`
6. **Ranking**: Sorts functions by line count and selects top 5 per repository
7. **Export**: Creates formatted Excel file with results
8. **Cleanup**: Automatically removes temporary cloned repositories

## Limitations

- Function size is measured by line count (including braces and blank lines)
- Nested functions are counted separately
- Very complex or unconventional syntax may not be detected
- Excludes common dependency directories (node_modules, target, build, etc.)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
