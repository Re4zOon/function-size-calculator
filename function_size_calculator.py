#!/usr/bin/env python3
"""
Function Size Calculator
Scans git repositories to find the largest functions in Node.js and Java codebases.
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
    """Represents information about a function."""
    
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
        """Parse JavaScript/TypeScript file to extract functions."""
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


class JavaParser:
    """Parser for Java functions/methods."""
    
    @staticmethod
    def parse_functions(file_path: str) -> List[FunctionInfo]:
        """Parse Java file to extract methods."""
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
    This function is designed to be called in parallel.
    Returns (repo_name, functions) tuple.
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
                if 'node_modules' in str(file_path) or '.git' in str(file_path):
                    continue
                
                functions = JavaScriptParser.parse_functions(str(file_path))
                # Make paths relative to repo root
                for func in functions:
                    func.file_path = os.path.relpath(func.file_path, local_path)
                all_functions.extend(functions)
        
        # Find all Java files
        for file_path in Path(local_path).rglob('*.java'):
            # Skip common build directories
            if any(d in str(file_path) for d in ['.git', 'target', 'build', 'out']):
                continue
            
            functions = JavaParser.parse_functions(str(file_path))
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
    def write_results(repo_results: Dict[str, List[FunctionInfo]], output_file: str):
        """Write results to Excel (XLSX) file with each repo on a separate tab."""
        wb = openpyxl.Workbook()
        # Remove default sheet
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
        
        for repo_name, functions in repo_results.items():
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
            
            # Sort functions by size (descending) and take top 5
            top_functions = sorted(functions, key=lambda f: f.size, reverse=True)[:5]
            
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
        description='Find the largest functions in git repositories (Node.js and Java)'
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
    
    args = parser.parse_args()
    
    # Validate jobs parameter
    if args.jobs < 1:
        print("Error: Number of parallel jobs must be at least 1")
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
    print(f"{'='*60}")
    
    repo_results = {}
    
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
                    
                    # Print summary
                    top_5 = sorted(functions, key=lambda f: f.size, reverse=True)[:5]
                    print(f"\nRepository: {repo}")
                    print(f"Found {len(functions)} functions. Top 5 largest:")
                    for i, func in enumerate(top_5, 1):
                        print(f"  {i}. {func.name} ({func.size} lines) - {func.file_path}")
                    print(f"{'='*60}")
            except Exception as e:
                print(f"Error processing repository {repo}: {e}")
    
    # Write results to Excel
    if repo_results:
        ExcelWriter.write_results(repo_results, args.output)
        print(f"\n{'='*60}")
        print(f"Done! Check {args.output} for detailed results.")
        print(f"{'='*60}")
    else:
        print("\nNo results to write. Please check the repository paths/URLs.")


if __name__ == '__main__':
    main()
