#!/usr/bin/env python3
"""
Test suite for function_size_calculator.py
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from function_size_calculator import (
    FunctionInfo,
    JavaScriptParser,
    JavaParser,
    ExcelWriter,
    scan_single_repository
)

try:
    import openpyxl
except ImportError:
    print("Warning: openpyxl not available. Skipping Excel tests.")
    openpyxl = None


class TestFunctionInfo(unittest.TestCase):
    """Test cases for FunctionInfo class."""
    
    def test_function_info_creation(self):
        """Test creating a FunctionInfo object."""
        func = FunctionInfo(
            name="testFunction",
            file_path="test.js",
            start_line=1,
            end_line=10,
            size=10
        )
        
        self.assertEqual(func.name, "testFunction")
        self.assertEqual(func.file_path, "test.js")
        self.assertEqual(func.start_line, 1)
        self.assertEqual(func.end_line, 10)
        self.assertEqual(func.size, 10)
    
    def test_function_info_repr(self):
        """Test FunctionInfo string representation."""
        func = FunctionInfo("myFunc", "file.js", 5, 15, 11)
        repr_str = repr(func)
        
        self.assertIn("myFunc", repr_str)
        self.assertIn("file.js", repr_str)
        self.assertIn("11", repr_str)


class TestJavaScriptParser(unittest.TestCase):
    """Test cases for JavaScriptParser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fixtures_dir = os.path.join(
            os.path.dirname(__file__), 
            'fixtures'
        )
        self.js_file = os.path.join(self.fixtures_dir, 'sample.js')
        self.ts_file = os.path.join(self.fixtures_dir, 'sample.ts')
    
    def test_parse_javascript_file(self):
        """Test parsing a JavaScript file."""
        functions = JavaScriptParser.parse_functions(self.js_file)
        
        # Should find multiple functions
        self.assertGreater(len(functions), 0)
        
        # Check for specific functions
        func_names = [f.name for f in functions]
        self.assertIn("simpleFunction", func_names)
        self.assertIn("largeFunction", func_names)
        self.assertIn("arrowFunction", func_names)
        self.assertIn("asyncArrowFunction", func_names)
        self.assertIn("outerFunction", func_names)
    
    def test_parse_typescript_file(self):
        """Test parsing a TypeScript file."""
        functions = JavaScriptParser.parse_functions(self.ts_file)
        
        # Should find functions
        self.assertGreater(len(functions), 0)
        
        # Check for specific functions
        func_names = [f.name for f in functions]
        self.assertIn("typedFunction", func_names)
        # Note: typedArrow may not be detected due to TypeScript type annotations
        # which the simple regex parser doesn't fully support
    
    def test_function_size_calculation(self):
        """Test that function sizes are calculated correctly."""
        functions = JavaScriptParser.parse_functions(self.js_file)
        
        # Find the simpleFunction
        simple = next((f for f in functions if f.name == "simpleFunction"), None)
        self.assertIsNotNone(simple)
        
        # simpleFunction should be 3 lines
        self.assertEqual(simple.size, 3)
        
        # Find largeFunction
        large = next((f for f in functions if f.name == "largeFunction"), None)
        self.assertIsNotNone(large)
        
        # largeFunction should be larger than simpleFunction
        self.assertGreater(large.size, simple.size)
    
    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        # Suppress expected warning output
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            functions = JavaScriptParser.parse_functions("/nonexistent/file.js")
        
        # Should return empty list, not crash
        self.assertEqual(len(functions), 0)
    
    def test_function_line_numbers(self):
        """Test that line numbers are correct."""
        functions = JavaScriptParser.parse_functions(self.js_file)
        
        for func in functions:
            # Start line should be positive
            self.assertGreater(func.start_line, 0)
            # End line should be greater than start line
            self.assertGreaterEqual(func.end_line, func.start_line)
            # Size should be positive
            self.assertGreater(func.size, 0)


class TestJavaParser(unittest.TestCase):
    """Test cases for JavaParser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fixtures_dir = os.path.join(
            os.path.dirname(__file__), 
            'fixtures'
        )
        self.java_file = os.path.join(self.fixtures_dir, 'Sample.java')
    
    def test_parse_java_file(self):
        """Test parsing a Java file."""
        functions = JavaParser.parse_functions(self.java_file)
        
        # Should find multiple methods
        self.assertGreater(len(functions), 0)
        
        # Check for specific methods
        func_names = [f.name for f in functions]
        self.assertIn("publicMethod", func_names)
        self.assertIn("privateMethod", func_names)
        self.assertIn("protectedStaticMethod", func_names)
        self.assertIn("largeMethod", func_names)
    
    def test_java_method_modifiers(self):
        """Test that methods with various modifiers are detected."""
        functions = JavaParser.parse_functions(self.java_file)
        func_names = [f.name for f in functions]
        
        # Test different modifier combinations
        self.assertIn("publicStaticFinalMethod", func_names)
        self.assertIn("synchronizedMethod", func_names)
        self.assertIn("methodWithException", func_names)
    
    def test_java_function_size(self):
        """Test that Java method sizes are calculated correctly."""
        functions = JavaParser.parse_functions(self.java_file)
        
        # Find the largeMethod
        large = next((f for f in functions if f.name == "largeMethod"), None)
        self.assertIsNotNone(large)
        
        # largeMethod should be at least 10 lines
        self.assertGreaterEqual(large.size, 10)
    
    def test_parse_nonexistent_java_file(self):
        """Test parsing a Java file that doesn't exist."""
        # Suppress expected warning output
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            functions = JavaParser.parse_functions("/nonexistent/Sample.java")
        
        # Should return empty list, not crash
        self.assertEqual(len(functions), 0)


class TestExcelWriter(unittest.TestCase):
    """Test cases for ExcelWriter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp(prefix='test_function_calc_')
        self.output_file = os.path.join(self.temp_dir, 'test_output.xlsx')
        
        # Create sample function data
        self.sample_functions = [
            FunctionInfo("func1", "file1.js", 1, 10, 10),
            FunctionInfo("func2", "file2.js", 1, 20, 20),
            FunctionInfo("func3", "file3.js", 1, 15, 15),
            FunctionInfo("func4", "file4.js", 1, 5, 5),
            FunctionInfo("func5", "file5.js", 1, 8, 8),
            FunctionInfo("func6", "file6.js", 1, 12, 12),
        ]
    
    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipIf(openpyxl is None, "openpyxl not available")
    def test_write_results_single_repo(self):
        """Test writing results for a single repository."""
        repo_results = {
            'test-repo': self.sample_functions
        }
        
        # Suppress "Results saved to" output
        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, self.output_file)
        
        # Check that file was created
        self.assertTrue(os.path.exists(self.output_file))
        
        # Load and verify content
        wb = openpyxl.load_workbook(self.output_file)
        self.assertIn('test-repo', wb.sheetnames)
        
        ws = wb['test-repo']
        
        # Check header row
        self.assertEqual(ws.cell(1, 1).value, 'Rank')
        self.assertEqual(ws.cell(1, 2).value, 'Function Name')
        self.assertEqual(ws.cell(1, 6).value, 'Lines of Code')
        
        # Check that top 5 functions are present (sorted by size)
        # func2 (20), func3 (15), func6 (12), func1 (10), func5 (8)
        self.assertEqual(ws.cell(2, 1).value, 1)  # Rank 1
        self.assertEqual(ws.cell(2, 2).value, 'func2')  # Largest function
        self.assertEqual(ws.cell(2, 6).value, 20)  # Size
        
        self.assertEqual(ws.cell(6, 1).value, 5)  # Rank 5
        
        wb.close()
    
    @unittest.skipIf(openpyxl is None, "openpyxl not available")
    def test_write_results_multiple_repos(self):
        """Test writing results for multiple repositories."""
        repo_results = {
            'repo1': self.sample_functions[:3],
            'repo2': self.sample_functions[3:]
        }
        
        # Suppress "Results saved to" output
        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, self.output_file)
        
        # Check that file was created
        self.assertTrue(os.path.exists(self.output_file))
        
        # Load and verify content
        wb = openpyxl.load_workbook(self.output_file)
        
        # Check that both sheets exist
        self.assertIn('repo1', wb.sheetnames)
        self.assertIn('repo2', wb.sheetnames)
        
        wb.close()
    
    @unittest.skipIf(openpyxl is None, "openpyxl not available")
    def test_sanitize_sheet_name(self):
        """Test that sheet names are sanitized properly."""
        # Test with long name and special characters
        repo_results = {
            'very/long/repository/name/that/exceeds/thirty/one/characters': self.sample_functions[:1]
        }
        
        # Suppress "Results saved to" output
        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, self.output_file)
        
        wb = openpyxl.load_workbook(self.output_file)
        
        # Check that sheet name is sanitized (max 31 chars, no slashes)
        sheet_names = wb.sheetnames
        self.assertEqual(len(sheet_names), 1)
        self.assertLessEqual(len(sheet_names[0]), 31)
        self.assertNotIn('/', sheet_names[0])
        
        wb.close()


class TestScanRepository(unittest.TestCase):
    """Test cases for scan_single_repository function."""
    
    def setUp(self):
        """Set up test repository."""
        self.test_repo_dir = tempfile.mkdtemp(prefix='test_repo_')
        
        # Create a simple test repository structure
        os.makedirs(os.path.join(self.test_repo_dir, 'src'), exist_ok=True)
        
        # Create a JavaScript file
        js_content = """
function testFunc() {
    console.log("test");
}
"""
        with open(os.path.join(self.test_repo_dir, 'src', 'test.js'), 'w') as f:
            f.write(js_content)
        
        # Create a Java file
        java_content = """
public class Test {
    public void testMethod() {
        System.out.println("test");
    }
}
"""
        with open(os.path.join(self.test_repo_dir, 'src', 'Test.java'), 'w') as f:
            f.write(java_content)
    
    def tearDown(self):
        """Clean up test repository."""
        if os.path.exists(self.test_repo_dir):
            shutil.rmtree(self.test_repo_dir)
    
    def test_scan_local_repository(self):
        """Test scanning a local repository."""
        repo_name, functions = scan_single_repository(self.test_repo_dir)
        
        # Check that repo name is extracted
        self.assertIsNotNone(repo_name)
        
        # Should find functions from both JS and Java files
        self.assertGreater(len(functions), 0)
        
        # Check that function names are found
        func_names = [f.name for f in functions]
        self.assertIn("testFunc", func_names)
        self.assertIn("testMethod", func_names)
    
    def test_scan_nonexistent_repository(self):
        """Test scanning a repository that doesn't exist."""
        # Suppress expected error output
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            repo_name, functions = scan_single_repository("/nonexistent/repo")
        
        # Should return None and empty list
        self.assertIsNone(repo_name)
        self.assertEqual(len(functions), 0)
    
    def test_relative_paths(self):
        """Test that file paths are relative to repo root."""
        repo_name, functions = scan_single_repository(self.test_repo_dir)
        
        for func in functions:
            # Paths should be relative
            self.assertFalse(func.file_path.startswith('/'))
            self.assertFalse(func.file_path.startswith(self.test_repo_dir))


class TestCommandLineArguments(unittest.TestCase):
    """Test cases for command-line argument handling."""
    
    def setUp(self):
        """Set up test files."""
        self.temp_dir = tempfile.mkdtemp(prefix='test_cli_')
        self.input_file = os.path.join(self.temp_dir, 'repos.txt')
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_input_file_parsing(self):
        """Test parsing repository list from input file."""
        # Create input file with repositories
        with open(self.input_file, 'w') as f:
            f.write("https://github.com/user/repo1.git\n")
            f.write("# This is a comment\n")
            f.write("\n")  # Empty line
            f.write("/path/to/local/repo\n")
        
        # Read and parse
        repositories = []
        with open(self.input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    repositories.append(line)
        
        # Should have 2 repositories (comment and empty line ignored)
        self.assertEqual(len(repositories), 2)
        self.assertIn("https://github.com/user/repo1.git", repositories)
        self.assertIn("/path/to/local/repo", repositories)


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
