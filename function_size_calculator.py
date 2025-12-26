#!/usr/bin/env python3
"""
Function Size Calculator
Scans git repositories to find the largest functions in Node.js and Java codebases.
Outputs results to an XLS file with each repository on a separate tab.
"""

import os
import re
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess

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


class RepositoryScanner:
    """Scans git repositories for functions."""
    
    def __init__(self):
        self.temp_dirs = []
    
    def clone_or_use_repo(self, repo_path: str) -> Tuple[str, bool]:
        """
        Clone repository if it's a URL, or use local path.
        Returns (local_path, is_temp) tuple.
        """
        if repo_path.startswith('http://') or repo_path.startswith('https://') or repo_path.startswith('git@'):
            # It's a remote repository - clone it
            temp_dir = tempfile.mkdtemp(prefix='function_calculator_')
            self.temp_dirs.append(temp_dir)
            
            print(f"Cloning repository: {repo_path}")
            try:
                subprocess.run(
                    ['git', 'clone', '--depth', '1', repo_path, temp_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
                return temp_dir, True
            except subprocess.CalledProcessError as e:
                print(f"Error cloning repository {repo_path}: {e}")
                return None, False
        else:
            # It's a local path
            if os.path.exists(repo_path):
                return repo_path, False
            else:
                print(f"Error: Local path does not exist: {repo_path}")
                return None, False
    
    def scan_repository(self, repo_path: str) -> List[FunctionInfo]:
        """Scan a repository and return all functions found."""
        local_path, is_temp = self.clone_or_use_repo(repo_path)
        
        if local_path is None:
            return []
        
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
        
        return all_functions
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
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
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Find the largest functions in git repositories (Node.js and Java)'
    )
    parser.add_argument(
        'repositories',
        nargs='+',
        help='Git repository URLs or local paths to scan'
    )
    parser.add_argument(
        '-o', '--output',
        default='function_sizes.xlsx',
        help='Output Excel (XLSX) file name (default: function_sizes.xlsx)'
    )
    
    args = parser.parse_args()
    
    scanner = RepositoryScanner()
    repo_results = {}
    
    try:
        for repo in args.repositories:
            print(f"\n{'='*60}")
            print(f"Scanning repository: {repo}")
            print(f"{'='*60}")
            
            functions = scanner.scan_repository(repo)
            
            # Use repository name as key
            repo_name = repo.split('/')[-1].replace('.git', '')
            if not repo_name:
                repo_name = 'repository'
            
            repo_results[repo_name] = functions
            
            # Print summary
            top_5 = sorted(functions, key=lambda f: f.size, reverse=True)[:5]
            print(f"\nFound {len(functions)} functions. Top 5 largest:")
            for i, func in enumerate(top_5, 1):
                print(f"  {i}. {func.name} ({func.size} lines) - {func.file_path}")
        
        # Write results to Excel
        if repo_results:
            ExcelWriter.write_results(repo_results, args.output)
            print(f"\n{'='*60}")
            print(f"Done! Check {args.output} for detailed results.")
            print(f"{'='*60}")
    
    finally:
        # Cleanup temporary directories
        scanner.cleanup()


if __name__ == '__main__':
    main()
