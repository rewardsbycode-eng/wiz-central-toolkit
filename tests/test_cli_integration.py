"""Integration tests for all wiz tools using subprocess."""
import subprocess


def run_wiz(tool, *args):
    """Helper to run wiz command and return result."""
    cmd = ["wiz", tool] + [str(arg) for arg in args]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestBannerwiz:
    """Tests for bannerwiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("bannerwiz", "--help")
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_basic_banner(self):
        """Test basic banner rendering."""
        result = run_wiz("bannerwiz", "HELLO")
        assert result.returncode == 0
        assert "\n" in result.stdout
        assert len(result.stdout) > 50

    def test_demo_mode(self):
        """Test demo mode works."""
        result = run_wiz("bannerwiz", "--demo")
        assert result.returncode == 0

    def test_list_fonts(self):
        """Test listing fonts."""
        result = run_wiz("bannerwiz", "--fonts")
        assert result.returncode == 0

    def test_list_styles(self):
        """Test listing styles."""
        result = run_wiz("bannerwiz", "--styles")
        assert result.returncode == 0


class TestDiffwiz:
    """Tests for diffwiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("diffwiz", "--help")
        assert result.returncode == 0

    def test_same_files(self, tmp_path):
        """Test diff on identical files."""
        file_a = tmp_path / "a.txt"
        file_b = tmp_path / "b.txt"
        file_a.write_text("same")
        file_b.write_text("same")

        result = run_wiz("diffwiz", "files", file_a, file_b)
        assert result.returncode != 2

    def test_summary_files(self, tmp_path):
        """Test summary command on files."""
        file_a = tmp_path / "a.txt"
        file_b = tmp_path / "b.txt"
        file_a.write_text("content a")
        file_b.write_text("content b")

        result = run_wiz("diffwiz", "summary", file_a, file_b)
        assert result.returncode != 2


class TestJsonwiz:
    """Tests for jsonwiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("jsonwiz", "--help")
        assert result.returncode == 0

    def test_validate_valid(self, tmp_path):
        """Test validating valid JSON."""
        sample_json = tmp_path / "sample.json"
        sample_json.write_text('{"ok": true}')

        result = run_wiz("jsonwiz", "validate", sample_json)
        assert result.returncode == 0

    def test_inspect(self, tmp_path):
        """Test inspecting JSON."""
        sample_json = tmp_path / "sample.json"
        sample_json.write_text('{"ok": true}')

        result = run_wiz("jsonwiz", "inspect", sample_json)
        assert result.returncode == 0


class TestPythonwiz:
    """Tests for pythonwiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("pythonwiz", "--help")
        assert result.returncode == 0

    def test_check_valid(self, tmp_path):
        """Test checking valid Python."""
        sample_python = tmp_path / "sample.py"
        sample_python.write_text("print('hello')\n")

        result = run_wiz("pythonwiz", "check", sample_python)
        assert result.returncode != 2


class TestRustwiz:
    """Tests for rustwiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("rustwiz", "--help")
        assert result.returncode == 0

    def test_check_project(self, tmp_path):
        """Test checking Rust project."""
        project = tmp_path / "sample-rust"
        src = project / "src"
        src.mkdir(parents=True)
        (project / "Cargo.toml").write_text(
            '[package]\nname = "sample-rust"\nversion = "0.1.0"\n'
            'edition = "2021"\n'
        )
        (src / "main.rs").write_text("fn main() {}\n")

        result = run_wiz("rustwiz", "check", project)
        assert result.returncode != 2


class TestReadwiz:
    """Tests for readwiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("readwiz", "--help")
        assert result.returncode == 0

    def test_verbs(self):
        """Test verbs command."""
        result = run_wiz("readwiz", "verbs")
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_law(self):
        """Test law command."""
        result = run_wiz("readwiz", "law")
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_check_command(self):
        """Test check command."""
        result = run_wiz("readwiz", "check", "pwd")
        assert result.returncode != 2


class TestTmuxwiz:
    """Tests for tmuxwiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("tmuxwiz", "--help")
        assert result.returncode == 0

    def test_list(self):
        """Test list command."""
        result = run_wiz("tmuxwiz", "list")
        assert result.returncode == 0

    def test_census(self):
        """Test census command."""
        result = run_wiz("tmuxwiz", "census")
        assert result.returncode == 0


class TestTodowiz:
    """Tests for todowiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("todowiz", "--help")
        assert result.returncode == 0


class TestWritewiz:
    """Tests for writewiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("writewiz", "--help")
        assert result.returncode == 0

    def test_law_digest(self):
        """Test law-digest command."""
        result = run_wiz("writewiz", "law-digest")
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0


class TestGodfatherwiz:
    """Tests for godfatherwiz."""

    def test_help(self):
        """Test help displays."""
        result = run_wiz("godfatherwiz", "--help")
        assert result.returncode == 0

    def test_siblings(self):
        """Test siblings command."""
        result = run_wiz("godfatherwiz", "siblings")
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_fleet(self):
        """Test fleet command."""
        result = run_wiz("godfatherwiz", "fleet")
        assert result.returncode == 0

    def test_routes(self):
        """Test routes command."""
        result = run_wiz("godfatherwiz", "routes")
        assert result.returncode == 0

    def test_status(self):
        """Test status command."""
        result = run_wiz("godfatherwiz", "status")
        assert result.returncode == 0

    def test_census(self):
        """Test census command."""
        result = run_wiz("godfatherwiz", "census")
        assert result.returncode == 0


class TestWizMain:
    """Tests for the main wiz command."""

    def test_main_help(self):
        """Test main wiz --help."""
        result = subprocess.run(["wiz", "--help"], capture_output=True, text=True)
        assert result.returncode == 0
