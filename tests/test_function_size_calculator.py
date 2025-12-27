#!/usr/bin/env python3
"""Pytest suite for function_size_calculator.py."""

import json
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from function_size_calculator import (
    ExcelWriter,
    FunctionInfo,
    JavaParser,
    JavaScriptParser,
    JSONWriter,
    print_progress_bar,
    scan_single_repository,
)

try:
    import openpyxl
except ImportError:  # pragma: no cover - dependency is optional in CI
    openpyxl = None


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures."""
    return Path(__file__).parent / "fixtures"


class TestFunctionInfo:
    """Tests for FunctionInfo class."""

    def test_function_info_creation(self):
        func = FunctionInfo(
            name="testFunction",
            file_path="test.js",
            start_line=1,
            end_line=10,
            size=10,
        )

        assert func.name == "testFunction"
        assert func.file_path == "test.js"
        assert func.start_line == 1
        assert func.end_line == 10
        assert func.size == 10

    def test_function_info_repr(self):
        func = FunctionInfo("myFunc", "file.js", 5, 15, 11)
        repr_str = repr(func)

        assert "myFunc" in repr_str
        assert "file.js" in repr_str
        assert "11" in repr_str

    def test_function_info_to_dict(self):
        func = FunctionInfo("testFunc", "test.py", 10, 20, 11)
        func_dict = func.to_dict()

        assert func_dict["name"] == "testFunc"
        assert func_dict["file_path"] == "test.py"
        assert func_dict["start_line"] == 10
        assert func_dict["end_line"] == 20
        assert func_dict["size"] == 11


class TestJavaScriptParser:
    """Tests for JavaScriptParser."""

    @pytest.fixture(autouse=True)
    def _setup(self, fixtures_dir: Path):
        self.js_file = fixtures_dir / "sample.js"
        self.ts_file = fixtures_dir / "sample.ts"

    def test_parse_javascript_file(self):
        functions = JavaScriptParser.parse_functions(str(self.js_file))

        assert len(functions) > 0

        func_names = [f.name for f in functions]
        assert "simpleFunction" in func_names
        assert "largeFunction" in func_names
        assert "arrowFunction" in func_names
        assert "asyncArrowFunction" in func_names
        assert "outerFunction" in func_names

    def test_parse_typescript_file(self):
        functions = JavaScriptParser.parse_functions(str(self.ts_file))

        assert len(functions) > 0

        func_names = [f.name for f in functions]
        assert "typedFunction" in func_names

    def test_function_size_calculation(self):
        functions = JavaScriptParser.parse_functions(str(self.js_file))

        simple = next((f for f in functions if f.name == "simpleFunction"), None)
        assert simple is not None
        assert simple.size == 3

        large = next((f for f in functions if f.name == "largeFunction"), None)
        assert large is not None
        assert large.size > simple.size

    def test_parse_nonexistent_file(self):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            functions = JavaScriptParser.parse_functions("/nonexistent/file.js")

        assert len(functions) == 0

    def test_function_line_numbers(self):
        functions = JavaScriptParser.parse_functions(str(self.js_file))

        for func in functions:
            assert func.start_line > 0
            assert func.end_line >= func.start_line
            assert func.size > 0


class TestJavaParser:
    """Tests for JavaParser."""

    @pytest.fixture(autouse=True)
    def _setup(self, fixtures_dir: Path):
        self.java_file = fixtures_dir / "Sample.java"

    def test_parse_java_file(self):
        functions = JavaParser.parse_functions(str(self.java_file))

        assert len(functions) > 0

        func_names = [f.name for f in functions]
        assert "publicMethod" in func_names
        assert "privateMethod" in func_names
        assert "protectedStaticMethod" in func_names
        assert "largeMethod" in func_names

    def test_java_method_modifiers(self):
        functions = JavaParser.parse_functions(str(self.java_file))
        func_names = [f.name for f in functions]

        assert "publicStaticFinalMethod" in func_names
        assert "synchronizedMethod" in func_names
        assert "methodWithException" in func_names

    def test_java_function_size(self):
        functions = JavaParser.parse_functions(str(self.java_file))

        large = next((f for f in functions if f.name == "largeMethod"), None)
        assert large is not None
        assert large.size >= 10

    def test_parse_nonexistent_java_file(self):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            functions = JavaParser.parse_functions("/nonexistent/Sample.java")

        assert len(functions) == 0


class TestExcelWriter:
    """Tests for ExcelWriter."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path):
        self.output_file = tmp_path / "test_output.xlsx"
        self.sample_functions = [
            FunctionInfo("func1", "file1.js", 1, 10, 10),
            FunctionInfo("func2", "file2.js", 1, 20, 20),
            FunctionInfo("func3", "file3.js", 1, 15, 15),
            FunctionInfo("func4", "file4.js", 1, 5, 5),
            FunctionInfo("func5", "file5.js", 1, 8, 8),
            FunctionInfo("func6", "file6.js", 1, 12, 12),
        ]

    @pytest.mark.skipif(openpyxl is None, reason="openpyxl not available")
    def test_write_results_single_repo(self):
        repo_results = {"test-repo": self.sample_functions}

        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, str(self.output_file))

        assert self.output_file.exists()

        wb = openpyxl.load_workbook(self.output_file)
        assert "test-repo" in wb.sheetnames

        ws = wb["test-repo"]
        assert ws.cell(1, 1).value == "Rank"
        assert ws.cell(1, 2).value == "Function Name"
        assert ws.cell(1, 6).value == "Lines of Code"

        assert ws.cell(2, 1).value == 1
        assert ws.cell(2, 2).value == "func2"
        assert ws.cell(2, 6).value == 20

        assert ws.cell(6, 1).value == 5
        wb.close()

    @pytest.mark.skipif(openpyxl is None, reason="openpyxl not available")
    def test_write_results_multiple_repos(self):
        repo_results = {
            "repo1": self.sample_functions[:3],
            "repo2": self.sample_functions[3:],
        }

        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, str(self.output_file))

        assert self.output_file.exists()

        wb = openpyxl.load_workbook(self.output_file)
        assert "repo1" in wb.sheetnames
        assert "repo2" in wb.sheetnames
        wb.close()

    @pytest.mark.skipif(openpyxl is None, reason="openpyxl not available")
    def test_sanitize_sheet_name(self):
        repo_results = {
            "very/long/repository/name/that/exceeds/thirty/one/characters": self.sample_functions[:1]
        }

        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, str(self.output_file))

        wb = openpyxl.load_workbook(self.output_file)
        sheet_names = wb.sheetnames
        assert len(sheet_names) == 1
        assert len(sheet_names[0]) <= 31
        assert "/" not in sheet_names[0]
        wb.close()

    @pytest.mark.skipif(openpyxl is None, reason="openpyxl not available")
    def test_top_n_parameter(self):
        repo_results = {"test-repo": self.sample_functions}

        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, str(self.output_file), top_n=3)

        wb = openpyxl.load_workbook(self.output_file)
        ws = wb["test-repo"]

        data_rows = 0
        for row in range(2, 10):
            value = ws.cell(row, 1).value
            if value and isinstance(value, int):
                data_rows += 1

        assert data_rows == 3
        wb.close()

    @pytest.mark.skipif(openpyxl is None, reason="openpyxl not available")
    def test_min_size_filter(self):
        repo_results = {"test-repo": self.sample_functions}

        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, str(self.output_file), top_n=10, min_size=10)

        wb = openpyxl.load_workbook(self.output_file)
        ws = wb["test-repo"]

        data_rows = 0
        for row in range(2, 10):
            value = ws.cell(row, 1).value
            if value and isinstance(value, int):
                data_rows += 1

        assert data_rows == 4

        for row in range(2, 6):
            size = ws.cell(row, 6).value
            if size is not None and isinstance(size, int):
                assert size >= 10

        wb.close()

    @pytest.mark.skipif(openpyxl is None, reason="openpyxl not available")
    def test_summary_statistics(self):
        repo_results = {"test-repo": self.sample_functions}

        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, str(self.output_file))

        wb = openpyxl.load_workbook(self.output_file)
        ws = wb["test-repo"]

        found_summary = any(ws.cell(row, 1).value == "Summary Statistics" for row in range(1, 20))
        assert found_summary, "Summary statistics section not found"
        wb.close()


class TestJSONWriter:
    """Tests for JSONWriter."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path):
        self.output_file = tmp_path / "test_output.json"
        self.sample_functions = [
            FunctionInfo("func1", "file1.js", 1, 10, 10),
            FunctionInfo("func2", "file2.js", 1, 20, 20),
            FunctionInfo("func3", "file3.js", 1, 15, 15),
            FunctionInfo("func4", "file4.js", 1, 5, 5),
            FunctionInfo("func5", "file5.js", 1, 8, 8),
        ]

    def test_write_results_single_repo(self):
        repo_results = {"test-repo": self.sample_functions}

        with redirect_stdout(StringIO()):
            JSONWriter.write_results(repo_results, str(self.output_file))

        assert self.output_file.exists()

        data = json.loads(self.output_file.read_text())

        assert "test-repo" in data
        assert "summary" in data["test-repo"]
        assert "top_functions" in data["test-repo"]

        summary = data["test-repo"]["summary"]
        assert summary["total_functions"] == 5
        assert summary["average_size"] > 0
        assert summary["largest_function_size"] == 20
        assert summary["smallest_function_size"] == 5

        top_funcs = data["test-repo"]["top_functions"]
        assert len(top_funcs) == 5
        assert top_funcs[0]["name"] == "func2"
        assert top_funcs[0]["size"] == 20

    def test_write_results_multiple_repos(self):
        repo_results = {
            "repo1": self.sample_functions[:3],
            "repo2": self.sample_functions[3:],
        }

        with redirect_stdout(StringIO()):
            JSONWriter.write_results(repo_results, str(self.output_file))

        assert self.output_file.exists()

        data = json.loads(self.output_file.read_text())
        assert "repo1" in data
        assert "repo2" in data

    def test_top_n_parameter(self):
        repo_results = {"test-repo": self.sample_functions}

        with redirect_stdout(StringIO()):
            JSONWriter.write_results(repo_results, str(self.output_file), top_n=3)

        data = json.loads(self.output_file.read_text())

        assert len(data["test-repo"]["top_functions"]) == 3

    def test_min_size_filter(self):
        repo_results = {"test-repo": self.sample_functions}

        with redirect_stdout(StringIO()):
            JSONWriter.write_results(repo_results, str(self.output_file), top_n=10, min_size=10)

        data = json.loads(self.output_file.read_text())

        top_funcs = data["test-repo"]["top_functions"]
        assert len(top_funcs) == 3
        assert all(func["size"] >= 10 for func in top_funcs)
        assert data["test-repo"]["summary"]["total_functions"] == 3

    def test_min_size_filter_multiple_repos(self):
        repo1_functions = [
            FunctionInfo("large_func", "file1.js", 1, 50, 50),
            FunctionInfo("medium_func", "file2.js", 1, 25, 25),
        ]
        repo2_functions = [
            FunctionInfo("small_func", "file3.js", 1, 5, 5),
            FunctionInfo("tiny_func", "file4.js", 1, 3, 3),
        ]

        repo_results = {"repo1": repo1_functions, "repo2": repo2_functions}

        with redirect_stdout(StringIO()):
            JSONWriter.write_results(repo_results, str(self.output_file), top_n=10, min_size=2)

        data = json.loads(self.output_file.read_text())

        assert data["repo1"]["summary"]["total_functions"] == 2
        assert data["repo2"]["summary"]["total_functions"] == 2
        assert len(data["repo1"]["top_functions"]) == 2
        assert len(data["repo2"]["top_functions"]) == 2


@pytest.fixture
def test_repository(tmp_path: Path) -> Path:
    """Create a temporary repository structure for scanning tests."""
    repo_dir = tmp_path / "test_repo"
    src_dir = repo_dir / "src"
    src_dir.mkdir(parents=True)

    js_content = """
function testFunc() {
    console.log("test");
}
"""
    (src_dir / "test.js").write_text(js_content)

    java_content = """
public class Test {
    public void testMethod() {
        System.out.println("test");
    }
}
"""
    (src_dir / "Test.java").write_text(java_content)

    return repo_dir


class TestScanRepository:
    """Tests for scan_single_repository function."""

    def test_scan_local_repository(self, test_repository: Path):
        repo_name, functions = scan_single_repository(str(test_repository))

        assert repo_name is not None
        assert len(functions) > 0

        func_names = [f.name for f in functions]
        assert "testFunc" in func_names
        assert "testMethod" in func_names

    def test_scan_nonexistent_repository(self):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            repo_name, functions = scan_single_repository("/nonexistent/repo")

        assert repo_name is None
        assert len(functions) == 0

    def test_relative_paths(self, test_repository: Path):
        _, functions = scan_single_repository(str(test_repository))

        for func in functions:
            assert not func.file_path.startswith("/")
            assert not func.file_path.startswith(str(test_repository))


class TestCommandLineArguments:
    """Tests for command-line argument handling."""

    def test_input_file_parsing(self, tmp_path: Path):
        input_file = tmp_path / "repos.txt"
        input_file.write_text(
            "https://github.com/user/repo1.git\n"
            "# This is a comment\n"
            "\n"
            "/path/to/local/repo\n"
        )

        repositories = []
        with open(input_file, encoding="utf-8") as file_handle:
            for line in file_handle:
                line = line.strip()
                if line and not line.startswith("#"):
                    repositories.append(line)

        assert len(repositories) == 2
        assert "https://github.com/user/repo1.git" in repositories
        assert "/path/to/local/repo" in repositories


class TestProgressBar:
    """Tests for print_progress_bar function."""

    def test_progress_bar_zero_total(self, capsys):
        """Progress bar should handle zero total gracefully."""
        print_progress_bar(0, 0, prefix="Test:", suffix="Done")
        captured = capsys.readouterr()
        # Should return early without printing
        assert captured.out == ""

    def test_progress_bar_partial_progress(self, capsys):
        """Progress bar should show partial progress."""
        print_progress_bar(5, 10, prefix="Progress:", suffix="Done")
        captured = capsys.readouterr()
        assert "50.0%" in captured.out
        assert "Progress:" in captured.out

    def test_progress_bar_complete(self, capsys):
        """Progress bar should print newline when complete."""
        print_progress_bar(10, 10, prefix="Progress:", suffix="Done")
        captured = capsys.readouterr()
        assert "100.0%" in captured.out
        # Should end with newline when complete
        assert captured.out.endswith("\n")


class TestEmptyResults:
    """Tests for handling empty results scenarios."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path):
        self.output_file = tmp_path / "test_output"

    @pytest.mark.skipif(openpyxl is None, reason="openpyxl not available")
    def test_write_empty_repo_excel(self):
        """ExcelWriter should handle empty function list."""
        repo_results = {"empty-repo": []}
        output_file = str(self.output_file) + ".xlsx"

        with redirect_stdout(StringIO()):
            ExcelWriter.write_results(repo_results, output_file)

        assert Path(output_file).exists()
        wb = openpyxl.load_workbook(output_file)
        ws = wb["empty-repo"]
        # Should still have header
        assert ws.cell(1, 1).value == "Rank"
        wb.close()

    def test_write_empty_repo_json(self):
        """JSONWriter should handle empty function list."""
        repo_results = {"empty-repo": []}
        output_file = str(self.output_file) + ".json"

        with redirect_stdout(StringIO()):
            JSONWriter.write_results(repo_results, output_file)

        assert Path(output_file).exists()
        data = json.loads(Path(output_file).read_text())
        assert "empty-repo" in data
        assert data["empty-repo"]["summary"] == {}
        assert data["empty-repo"]["top_functions"] == []
