#!/usr/bin/env python3
"""
Function Size Calculator
Scans git repositories to find the largest functions in Node.js, Java, and Python codebases.
Outputs results to an Excel (XLSX) file with each repository on a separate tab.
"""

import argparse
import os
import re
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
except ImportError:
    print("Error: openpyxl is required. Install it with: pip install openpyxl")
    sys.exit(1)


class FunctionInfo:
    """
    Represents information about a function or method.
    
    Attributes:
        name: The name of the function/method
        file_path: Path to the file containing the function
        start_line: Line number where the function starts (1-indexed)
        end_line: Line number where the function ends (1-indexed)
        size: Total number of lines in the function
    """
    
    def __init__(self, name: str, file_path: str, start_line: int, end_line: int, size: int):
        self.name = name
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.size = size
    
    def __repr__(self):
        return f"FunctionInfo({self.name}, {self.file_path}, lines={self.size})"


class JavaScriptParser:
    """Parser for JavaScript/TypeScript functions."""
    
    @staticmethod
    def parse_functions(file_path: str) -> List[FunctionInfo]:
        """
        Parse JavaScript/TypeScript file to extract functions.
        
        Supports various function patterns including:
        - Function declarations: function name() {}
        - Arrow functions: const name = () => {}
        - Methods: name() {}
        - Class methods with modifiers: async name() {}
        
        Args:
            file_path: Path to the JavaScript/TypeScript file
            
        Returns:
            List of FunctionInfo objects for all detected functions
        """
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return functions
        
        lines = content.split('\n')
        
        # Patterns for different function declarations
        patterns = [
            # function declaration: function name() {}
            (r'^\s*function\s+(\w+)\s*\(', 'function'),
            # arrow function: const name = () => {}
            (r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', 'arrow'),
            # method: name() {}
            (r'^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{', 'method'),
            # class method: async name() {}
            (r'^\s*(?:public|private|protected|static)?\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{', 'class_method'),
        ]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            for pattern, func_type in patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    start_line = i + 1
                    
                    # Find the end of the function by counting braces
                    brace_count = line.count('{') - line.count('}')
                    end_line = i
                    
                    j = i + 1
                    while j < len(lines) and brace_count > 0:
                        brace_count += lines[j].count('{') - lines[j].count('}')
                        end_line = j
                        j += 1
                    
                    if brace_count == 0 and end_line > i:
                        size = end_line - i + 1
                        functions.append(FunctionInfo(
                            name=func_name,
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line + 1,
                            size=size
                        ))
                    break
            i += 1
        
        return functions


class PythonParser:
    """Parser for Python functions."""
    
    @staticmethod
    def parse_functions(file_path: str) -> List[FunctionInfo]:
        """
        Parse Python file to extract functions.
        
        Uses indentation-based parsing to detect function boundaries.
        Supports both regular functions and methods.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of FunctionInfo objects for all detected functions
        """
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return functions
        
        lines = content.split('\n')
        
        # Pattern for Python function/method definitions (including async)
        # Matches: def function_name(...): or async def function_name(...):
        func_pattern = r'^\s*(?:async\s+)?def\s+(\w+)\s*\('
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            match = re.search(func_pattern, line)
            if match:
                func_name = match.group(1)
                start_line = i + 1
                
                # Get the base indentation level of the function definition
                base_indent = len(line) - len(line.lstrip())
                
                # Find where the function signature ends (look for ':')
                # Handle multi-line signatures by checking for unmatched parentheses
                j = i
                paren_count = line.count('(') - line.count(')')
                while j < len(lines):
                    if ':' in lines[j] and paren_count == 0:
                        break
                    j += 1
                    if j < len(lines):
                        paren_count += lines[j].count('(') - lines[j].count(')')
                
                # Now find where the function body ends
                j += 1
                end_line = i  # Initialize to function start
                
                while j < len(lines):
                    current_line = lines[j]
                    
                    # Skip blank lines and comments
                    if current_line.strip() == '' or current_line.strip().startswith('#'):
                        j += 1
                        continue
                    
                    # Check indentation
                    current_indent = len(current_line) - len(current_line.lstrip())
                    
                    # If we're back to the base level or lower, function has ended
                    if current_indent <= base_indent:
                        break
                    
                    end_line = j
                    j += 1
                
                if end_line >= i:
                    size = end_line - i + 1
                    functions.append(FunctionInfo(
                        name=func_name,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line + 1,
                        size=size
                    ))
            i += 1
        
        return functions


class JavaParser:
    """Parser for Java functions/methods."""
    
    @staticmethod
    def parse_functions(file_path: str) -> List[FunctionInfo]:
        """
        Parse Java file to extract methods.
        
        Supports methods with various modifiers including:
        - Access modifiers: public, private, protected
        - Other modifiers: static, final, synchronized
        - Generic return types
        - Throws clauses
        
        Args:
            file_path: Path to the Java file
            
        Returns:
            List of FunctionInfo objects for all detected methods
        """
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return functions
        
        lines = content.split('\n')
        
        # Pattern for Java methods
        # Matches: [modifiers] returnType methodName(params) {
        method_pattern = r'^\s*(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(?:synchronized)?\s*[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{'
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            match = re.search(method_pattern, line)
            if match:
                func_name = match.group(1)
                start_line = i + 1
                
                # Find the end of the method by counting braces
                brace_count = line.count('{') - line.count('}')
                end_line = i
                
                j = i + 1
                while j < len(lines) and brace_count > 0:
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    end_line = j
                    j += 1
                
                if brace_count == 0 and end_line > i:
                    size = end_line - i + 1
                    functions.append(FunctionInfo(
                        name=func_name,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line + 1,
                        size=size
                    ))
            i += 1
        
        return functions


def scan_single_repository(repo_path: str) -> Tuple[str, List[FunctionInfo]]:
    """
    Scan a single repository and return results.
    
    This function is designed to be called in parallel. It handles both remote
    repositories (which are cloned to a temporary directory) and local repositories.
    
    Args:
        repo_path: URL of a git repository or path to a local repository
        
    Returns:
        A tuple of (repository_name, list_of_functions). Returns (None, []) on error.
    """
    temp_dir = None
    try:
        # Clone or use local repo
        if repo_path.startswith('http://') or repo_path.startswith('https://') or repo_path.startswith('git@'):
            # It's a remote repository - clone it
            temp_dir = tempfile.mkdtemp(prefix='function_calculator_')
            
            print(f"Cloning repository: {repo_path}")
            try:
                subprocess.run(
                    ['git', 'clone', '--depth', '1', repo_path, temp_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
                local_path = temp_dir
            except subprocess.CalledProcessError as e:
                print(f"Error cloning repository {repo_path}: {e}")
                return None, []
        else:
            # It's a local path
            if os.path.exists(repo_path):
                local_path = repo_path
            else:
                print(f"Error: Local path does not exist: {repo_path}")
                return None, []
        
        all_functions = []
        
        # Find all JavaScript/TypeScript files
        js_extensions = ['.js', '.jsx', '.ts', '.tsx', '.mjs']
        for ext in js_extensions:
            for file_path in Path(local_path).rglob(f'*{ext}'):
                # Skip node_modules and other common directories
                path_parts = file_path.parts
                if 'node_modules' in path_parts or '.git' in path_parts:
                    continue
                
                functions = JavaScriptParser.parse_functions(str(file_path))
                # Make paths relative to repo root
                for func in functions:
                    func.file_path = os.path.relpath(func.file_path, local_path)
                all_functions.extend(functions)
        
        # Find all Java files
        for file_path in Path(local_path).rglob('*.java'):
            # Skip common build directories
            path_parts = file_path.parts
            if any(d in path_parts for d in ['.git', 'target', 'build', 'out']):
                continue
            
            functions = JavaParser.parse_functions(str(file_path))
            # Make paths relative to repo root
            for func in functions:
                func.file_path = os.path.relpath(func.file_path, local_path)
            all_functions.extend(functions)
        
        # Find all Python files
        for file_path in Path(local_path).rglob('*.py'):
            # Skip common directories and virtual environments
            path_parts = file_path.parts
            if any(d in path_parts for d in ['.git', '__pycache__', 'venv', 'env', '.venv', 'site-packages']):
                continue
            
            functions = PythonParser.parse_functions(str(file_path))
            # Make paths relative to repo root
            for func in functions:
                func.file_path = os.path.relpath(func.file_path, local_path)
            all_functions.extend(functions)
        
        # Get repository name
        repo_name = os.path.basename(repo_path.rstrip('/').replace('.git', ''))
        if not repo_name:
            repo_name = 'repository'
        
        return repo_name, all_functions
    
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


class ExcelWriter:
    """Writes results to Excel (XLSX) file."""
    
    @staticmethod
    def write_results(repo_results: Dict[str, List[FunctionInfo]], output_file: str, 
                     top_n: int = 5, min_size: int = 1):
        """
        Write results to Excel (XLSX) file with each repo on a separate tab.
        
        Args:
            repo_results: Dictionary mapping repository names to lists of functions
            output_file: Path to the output Excel file
            top_n: Number of top functions to include per repository
            min_size: Minimum function size (in lines) to include
        """
        wb = openpyxl.Workbook()
        # Remove default sheet
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
        
        for repo_name, functions in repo_results.items():
            # Filter by minimum size
            filtered_functions = [f for f in functions if f.size >= min_size]
            
            # Create sanitized sheet name (Excel has 31 char limit and special char restrictions)
            sheet_name = repo_name.replace('/', '_').replace('\\', '_')
            if len(sheet_name) > 31:
                sheet_name = sheet_name[:31]
            
            ws = wb.create_sheet(title=sheet_name)
            
            # Add header row
            headers = ['Rank', 'Function Name', 'File Path', 'Start Line', 'End Line', 'Lines of Code']
            ws.append(headers)
            
            # Style header
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_font = Font(bold=True, color='FFFFFF')
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            
            # Sort functions by size (descending) and take top N
            top_functions = sorted(filtered_functions, key=lambda f: f.size, reverse=True)[:top_n]
            
            # Add data rows
            for rank, func in enumerate(top_functions, 1):
                ws.append([
                    rank,
                    func.name,
                    func.file_path,
                    func.start_line,
                    func.end_line,
                    func.size
                ])
            
            # Add summary statistics at the bottom
            if filtered_functions:
                ws.append([])  # Empty row
                ws.append(['Summary Statistics'])
                ws.append(['Total Functions Found:', len(filtered_functions)])
                ws.append(['Average Function Size:', 
                          f"{sum(f.size for f in filtered_functions) / len(filtered_functions):.1f} lines"])
                ws.append(['Largest Function:', max(f.size for f in filtered_functions)])
                ws.append(['Smallest Function:', min(f.size for f in filtered_functions)])
            
            # Adjust column widths
            ws.column_dimensions['A'].width = 8
            ws.column_dimensions['B'].width = 30
            ws.column_dimensions['C'].width = 50
            ws.column_dimensions['D'].width = 12
            ws.column_dimensions['E'].width = 12
            ws.column_dimensions['F'].width = 15
        
        wb.save(output_file)
        print(f"\nResults saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Find the largest functions in git repositories (Node.js, Java, and Python)'
    )
    parser.add_argument(
        'repositories',
        nargs='*',
        help='Git repository URLs or local paths to scan'
    )
    parser.add_argument(
        '-i', '--input-file',
        help='File containing list of repository URLs/paths (one per line)'
    )
    parser.add_argument(
        '-o', '--output',
        default='function_sizes.xlsx',
        help='Output Excel (XLSX) file name (default: function_sizes.xlsx)'
    )
    parser.add_argument(
        '-j', '--jobs',
        type=int,
        default=4,
        help='Number of parallel jobs (default: 4)'
    )
    parser.add_argument(
        '-n', '--top-n',
        type=int,
        default=5,
        help='Number of top largest functions to report per repository (default: 5)'
    )
    parser.add_argument(
        '-m', '--min-size',
        type=int,
        default=1,
        help='Minimum function size in lines to include (default: 1)'
    )
    
    args = parser.parse_args()
    
    # Validate jobs parameter
    if args.jobs < 1:
        print("Error: Number of parallel jobs must be at least 1")
        sys.exit(1)
    
    # Validate top-n parameter
    if args.top_n < 1:
        print("Error: Number of top functions must be at least 1")
        sys.exit(1)
    
    # Validate min-size parameter
    if args.min_size < 1:
        print("Error: Minimum function size must be at least 1")
        sys.exit(1)
    
    # Validate output file extension
    if not args.output.endswith('.xlsx'):
        print("Error: Output file must have .xlsx extension")
        sys.exit(1)
    
    # Collect repositories from command line and/or input file
    repositories = list(args.repositories) if args.repositories else []
    
    if args.input_file:
        try:
            with open(args.input_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        repositories.append(line)
        except FileNotFoundError:
            print(f"Error: Input file not found: {args.input_file}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading input file: {e}")
            sys.exit(1)
    
    if not repositories:
        parser.print_help()
        print("\nError: No repositories specified. Provide repositories via command line or --input-file")
        sys.exit(1)
    
    print(f"Scanning {len(repositories)} repositories using {args.jobs} parallel jobs...")
    print(f"Configuration: Top {args.top_n} functions, Minimum size: {args.min_size} lines")
    print(f"{'='*60}")
    
    repo_results = {}
    completed_count = 0
    
    # Process repositories in parallel
    with ProcessPoolExecutor(max_workers=args.jobs) as executor:
        # Submit all tasks
        future_to_repo = {executor.submit(scan_single_repository, repo): repo for repo in repositories}
        
        # Process completed tasks
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                repo_name, functions = future.result()
                
                if repo_name is not None:
                    repo_results[repo_name] = functions
                    completed_count += 1
                    
                    # Filter by minimum size for display
                    filtered = [f for f in functions if f.size >= args.min_size]
                    
                    # Print summary
                    top_n_display = sorted(filtered, key=lambda f: f.size, reverse=True)[:args.top_n]
                    print(f"\n[{completed_count}/{len(repositories)}] Repository: {repo}")
                    print(f"Found {len(functions)} functions ({len(filtered)} >= {args.min_size} lines). Top {args.top_n} largest:")
                    for i, func in enumerate(top_n_display, 1):
                        print(f"  {i}. {func.name} ({func.size} lines) - {func.file_path}")
                    print(f"{'='*60}")
            except Exception as e:
                print(f"Error processing repository {repo}: {e}")
    
    # Write results to Excel
    if repo_results:
        ExcelWriter.write_results(repo_results, args.output, args.top_n, args.min_size)
        print(f"\n{'='*60}")
        print(f"Done! Check {args.output} for detailed results.")
        print(f"{'='*60}")
    else:
        print("\nNo results to write. Please check the repository paths/URLs.")


if __name__ == '__main__':
    main()
