import re
import subprocess
import sys

PATTERNS = {
    "OpenAI key": r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}",
    "Groq key": r"gsk_[A-Za-z0-9]{20,}",
    "GitHub token": r"github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{30,}",
    "Google key": r"AIza[0-9A-Za-z_-]{35}",
    "Password in a database URL": r"postgres(?:ql)?://[^:/\s]+:([^@\s]+)@",
    "Password in SQL": r"PASSWORD\s+'([^']+)'",
}
PLACEHOLDERS = {"CHOOSE_A_PASSWORD", "YOUR_POSTGRES_PASSWORD"}


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False).stdout


def find_secrets(text):
    found = []
    for name, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text):
            secret = match.group(match.lastindex or 0)
            if secret not in PLACEHOLDERS:
                found.append((name, secret[:4] + "***"))
    return found


def check_tracked_files():
    problems = []
    for path in git("ls-files").splitlines():
        if path.endswith((".pdf", ".docx", ".png")) or path == "scripts/check_secrets.py":
            continue
        with open(path, encoding="utf-8", errors="replace") as file:
            for number, line in enumerate(file, start=1):
                for name, masked in find_secrets(line):
                    problems.append(f"{path}:{number} {name} ({masked})")
    return problems


def check_history():
    problems = []
    commit = ""
    for line in git("log", "-p", "--all", "--format=commit %h").splitlines():
        if line.startswith("commit "):
            commit = line.split()[1]
        elif line.startswith("+") and not line.startswith("+++") and "check_secrets" not in line:
            for name, masked in find_secrets(line):
                problems.append(f"commit {commit}: {name} ({masked})")
    return sorted(set(problems))


def check_env_file():
    problems = []
    if not git("check-ignore", ".env").strip():
        problems.append(".env is not in .gitignore")
    if git("log", "--all", "--format=%h", "--", ".env").strip():
        problems.append(".env was committed in the past")
    return problems


def main():
    sections = {
        ".env file": check_env_file(),
        "Files in the repo now": check_tracked_files(),
        "Git history": check_history(),
    }
    for title, problems in sections.items():
        print(f"{title}: {'OK' if not problems else 'FOUND ' + str(len(problems))}")
        for problem in problems:
            print(f"   - {problem}")

    if any(sections.values()):
        sys.exit(1)
    print("No secrets found.")


if __name__ == "__main__":
    main()
