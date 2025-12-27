# Function Size Calculator

A Python tool that scans git repositories to find the largest functions in Java, Node.js, Python, and C# codebases. The results are exported to an Excel (XLSX) or JSON file with each repository on a separate tab.

## Features

- Scans multiple git repositories (local or remote)
- **Parallel processing** for efficient scanning of multiple repositories
- Supports Node.js (JavaScript, TypeScript), Java, Python, and **C#**
- **Memory-efficient streaming** handles very large files without loading entire files into memory
- **Multiple output formats**: Excel (XLSX) and JSON
- **Configurable number of top functions** to report (default: 5)
- **Minimum function size filter** to exclude trivial functions
- **Summary statistics** for each repository
- **Git clone timeout** to prevent hanging on problematic repositories
- Exports results to Excel format with:
  - Each repository on a separate tab
  - Function name, file path, line numbers, and size
  - Summary statistics (total functions, average size, largest/smallest)
  - Formatted headers and auto-sized columns
- JSON export option for programmatic consumption
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

Run all tests (pytest is configured for colorful, verbose output):
```bash
pytest
```

Run specific test class:
```bash
pytest tests/test_function_size_calculator.py -k TestJavaScriptParser
```

Run a specific test:
```bash
pytest tests/test_function_size_calculator.py -k test_parse_javascript_file
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

8. Report top 10 functions instead of default 5:
```bash
python function_size_calculator.py -i repos.txt -n 10
```

9. Filter out small functions (e.g., exclude functions smaller than 10 lines):
```bash
python function_size_calculator.py -i repos.txt -m 10
```

10. Combine multiple options:
```bash
python function_size_calculator.py -i repos.txt -n 20 -m 5 -j 8 -o detailed_analysis.xlsx
```

11. Generate JSON output instead of Excel:
```bash
python function_size_calculator.py -i repos.txt -o results.json
```

12. Explicitly specify output format:
```bash
python function_size_calculator.py -i repos.txt -f json -o results.json
```

### Command-Line Options

- `repositories`: One or more git repository URLs or local paths (optional if using -i)
- `-i`, `--input-file`: File containing list of repository URLs/paths (one per line, comments with # are supported)
- `-o`, `--output`: Output file name (default: `function_sizes.xlsx`). Use .json extension for JSON format.
- `-f`, `--format`: Output format - `xlsx`, `json`, or `auto` (default: auto - detect from file extension)
- `-j`, `--jobs`: Number of parallel jobs for scanning repositories (default: 4)
- `-n`, `--top-n`: Number of top largest functions to report per repository (default: 5)
- `-m`, `--min-size`: Minimum function size in lines to include (default: 1)
- `-h`, `--help`: Show help message

## Output Formats

### Excel (XLSX)
The default output format. Generates an Excel file with the following structure:

- **Each repository gets its own tab** named after the repository
- **Columns in each tab:**
  - Rank: Position in top N (1-N based on --top-n parameter)
  - Function Name: Name of the function/method
  - File Path: Relative path to the file containing the function
  - Start Line: Line number where the function starts
  - End Line: Line number where the function ends
  - Lines of Code: Total lines in the function
- **Summary Statistics:**
  - Total Functions Found
  - Average Function Size
  - Largest Function
  - Smallest Function

### JSON
An alternative output format for programmatic consumption. Structure:

```json
{
  "repository-name": {
    "summary": {
      "total_functions": 100,
      "average_size": 15.5,
      "largest_function_size": 250,
      "smallest_function_size": 3
    },
    "top_functions": [
      {
        "name": "functionName",
        "file_path": "path/to/file.js",
        "start_line": 10,
        "end_line": 50,
        "size": 41
      }
    ]
  }
}
```

To use JSON format, either:
- Use the `.json` extension: `-o results.json`
- Explicitly specify format: `-f json -o results.json`

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

### Python
- Function definitions: `def function_name():`
- Async functions: `async def function_name():`
- Class methods: `def method(self):`
- Static and class methods
- Supports: `.py` files

### C#
- Methods with various modifiers: `public async Task<string> Method() {}`
- Access modifiers: public, private, protected, internal
- Other modifiers: static, virtual, override, abstract, sealed, async
- Generic return types
- Supports: `.cs` files

## How It Works

1. **Repository Access**: Clones remote repositories to temporary directories or uses local paths
2. **Parallel Processing**: Scans multiple repositories concurrently for improved performance
3. **File Discovery**: Recursively finds all relevant source files (skips `node_modules`, `.git`, `target`, `__pycache__`, etc.)
4. **Function Parsing**: Uses streaming parsers with regex patterns and syntax-based parsing to identify function/method declarations
   - **Memory-Efficient**: Processes files line-by-line without loading entire files into memory, allowing analysis of very large files
   - **JavaScript/TypeScript/Java**: Counts lines by tracking brace pairs `{}`
   - **Python**: Uses indentation-based parsing
5. **Size Calculation**: Counts lines from function start to end
6. **Filtering**: Applies minimum size filter to exclude trivial functions
7. **Ranking**: Sorts functions by line count and selects top N per repository
8. **Export**: Creates formatted Excel or JSON file with results and summary statistics
9. **Cleanup**: Automatically removes temporary cloned repositories

## Limitations

- Function size is measured by line count (including braces and blank lines)
- Nested functions are counted separately
- Very complex or unconventional syntax may not be detected
- Excludes common dependency directories (node_modules, target, build, etc.)

## Test Results

![Tests](https://github.com/Re4zOon/function-size-calculator/actions/workflows/test.yml/badge.svg)

```
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0 -- /opt/hostedtoolcache/Python/3.12.12/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/function-size-calculator/function-size-calculator
configfile: pytest.ini
testpaths: tests
collecting ... collected 38 items

tests/test_function_size_calculator.py::TestFunctionInfo::test_function_info_creation PASSED [  2%]
tests/test_function_size_calculator.py::TestFunctionInfo::test_function_info_repr PASSED [  5%]
tests/test_function_size_calculator.py::TestFunctionInfo::test_function_info_to_dict PASSED [  7%]
tests/test_function_size_calculator.py::TestJavaScriptParser::test_parse_javascript_file PASSED [ 10%]
tests/test_function_size_calculator.py::TestJavaScriptParser::test_parse_typescript_file PASSED [ 13%]
tests/test_function_size_calculator.py::TestJavaScriptParser::test_function_size_calculation PASSED [ 15%]
tests/test_function_size_calculator.py::TestJavaScriptParser::test_parse_nonexistent_file PASSED [ 18%]
tests/test_function_size_calculator.py::TestJavaScriptParser::test_function_line_numbers PASSED [ 21%]
tests/test_function_size_calculator.py::TestJavaParser::test_parse_java_file PASSED [ 23%]
tests/test_function_size_calculator.py::TestJavaParser::test_java_method_modifiers PASSED [ 26%]
tests/test_function_size_calculator.py::TestJavaParser::test_java_function_size PASSED [ 28%]
tests/test_function_size_calculator.py::TestJavaParser::test_parse_nonexistent_java_file PASSED [ 31%]
tests/test_function_size_calculator.py::TestCSharpParser::test_parse_csharp_file PASSED [ 34%]
tests/test_function_size_calculator.py::TestCSharpParser::test_csharp_method_modifiers PASSED [ 36%]
tests/test_function_size_calculator.py::TestCSharpParser::test_csharp_function_size PASSED [ 39%]
tests/test_function_size_calculator.py::TestCSharpParser::test_parse_nonexistent_csharp_file PASSED [ 42%]
tests/test_function_size_calculator.py::TestCSharpParser::test_csharp_method_with_brace_on_same_line PASSED [ 44%]
tests/test_function_size_calculator.py::TestCSharpParser::test_csharp_pending_method_discarded_on_new_declaration PASSED [ 47%]
tests/test_function_size_calculator.py::TestPythonParser::test_parse_python_file PASSED [ 50%]
tests/test_function_size_calculator.py::TestPythonParser::test_python_class_methods PASSED [ 52%]
tests/test_function_size_calculator.py::TestPythonParser::test_python_function_size PASSED [ 55%]
tests/test_function_size_calculator.py::TestPythonParser::test_multiline_signature PASSED [ 57%]
tests/test_function_size_calculator.py::TestPythonParser::test_parse_nonexistent_python_file PASSED [ 60%]
tests/test_function_size_calculator.py::TestExcelWriter::test_write_results_single_repo PASSED [ 63%]
tests/test_function_size_calculator.py::TestExcelWriter::test_write_results_multiple_repos PASSED [ 65%]
tests/test_function_size_calculator.py::TestExcelWriter::test_sanitize_sheet_name PASSED [ 68%]
tests/test_function_size_calculator.py::TestExcelWriter::test_top_n_parameter PASSED [ 71%]
tests/test_function_size_calculator.py::TestExcelWriter::test_min_size_filter PASSED [ 73%]
tests/test_function_size_calculator.py::TestExcelWriter::test_summary_statistics PASSED [ 76%]
tests/test_function_size_calculator.py::TestJSONWriter::test_write_results_single_repo PASSED [ 78%]
tests/test_function_size_calculator.py::TestJSONWriter::test_write_results_multiple_repos PASSED [ 81%]
tests/test_function_size_calculator.py::TestJSONWriter::test_top_n_parameter PASSED [ 84%]
tests/test_function_size_calculator.py::TestJSONWriter::test_min_size_filter PASSED [ 86%]
tests/test_function_size_calculator.py::TestJSONWriter::test_min_size_filter_multiple_repos PASSED [ 89%]
tests/test_function_size_calculator.py::TestScanRepository::test_scan_local_repository PASSED [ 92%]
tests/test_function_size_calculator.py::TestScanRepository::test_scan_nonexistent_repository PASSED [ 94%]
tests/test_function_size_calculator.py::TestScanRepository::test_relative_paths PASSED [ 97%]
tests/test_function_size_calculator.py::TestCommandLineArguments::test_input_file_parsing PASSED [100%]

============================== 38 passed in 0.36s ==============================
```

*Last updated: 2025-12-27 04:14:22 UTC*
## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
