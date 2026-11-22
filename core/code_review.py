from pathlib import Path

from core.claude import Claude

MIN_FILES = 7
MAX_FILES = 40  # cost guard
MAX_FILE_CHARS = 30_000  # larger files are truncated

SOURCE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
    ".c", ".cpp", ".h", ".cs", ".rb", ".php", ".kt", ".swift",
}
SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    "dist", "build", ".idea", ".vscode",
}

FILE_SYSTEM = (
    "You are a senior code reviewer. Review the file for bugs, security "
    "issues, error handling, performance and maintainability. "
    "Output markdown: a bullet list of findings, each as "
    "`[HIGH|MED|LOW] line/func - problem - fix`. Be concise. "
    "If nothing relevant, say 'No issues'."
)
SUMMARY_SYSTEM = (
    "You are a lead reviewer. Given per-file reviews, write a short "
    "markdown report: overall verdict, top cross-cutting risks "
    "(max 5, ordered by severity), and recommended next steps."
)


class CodeReviewAgent:
    def __init__(self, claude: Claude):
        self.claude = claude

    def collect_files(self, directory: str) -> list[Path]:
        root = Path(directory)
        if not root.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        files = sorted(
            p
            for p in root.rglob("*")
            if p.is_file()
            and p.suffix.lower() in SOURCE_EXTS
            and not SKIP_DIRS.intersection(p.relative_to(root).parts)
        )
        if len(files) < MIN_FILES:
            raise ValueError(
                f"Need at least {MIN_FILES} source files, found {len(files)} "
                f"in {directory}"
            )
        return files[:MAX_FILES]

    def _ask(self, system: str, prompt: str) -> str:
        messages: list = []
        self.claude.add_user_message(messages, prompt)
        reply = self.claude.chat(messages, system=system, temperature=0.0)
        return self.claude.text_from_message(reply)

    def review_file(self, path: Path, root: Path) -> str:
        code = path.read_text(encoding="utf-8", errors="replace")
        truncated = len(code) > MAX_FILE_CHARS
        code = code[:MAX_FILE_CHARS]
        rel = path.relative_to(root)
        note = "\n(file truncated)" if truncated else ""
        return self._ask(
            FILE_SYSTEM, f"<file path=\"{rel}\">\n{code}\n</file>{note}"
        )

    def review(self, directory: str) -> str:
        root = Path(directory)
        files = self.collect_files(directory)

        sections = []
        for path in files:
            rel = path.relative_to(root)
            print(f"Reviewing {rel} ...")
            sections.append(f"## {rel}\n{self.review_file(path, root)}")

        per_file = "\n\n".join(sections)
        summary = self._ask(SUMMARY_SYSTEM, per_file)
        return f"# Code review: {root}\n\n{summary}\n\n---\n\n{per_file}\n"
