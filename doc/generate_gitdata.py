
import subprocess

def run_command (cmd: str):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.strip().decode("utf-8")
def generate_gitdata (version_root):
    git_branch   = run_command("git rev-parse --abbrev-ref HEAD".split())
    all_branches = run_command([ "bash", "-c", "git branch -r | cut -c 3- | sed 's/origin\\///g'" ]).split("\n")

    return {
        "git_branch": git_branch.strip(),
        "all_branches": [
            {
                "name": branch.strip(),
                "path": version_root if branch == "release" else version_root + branch
            }
            for branch in all_branches if branch != "gh-pages"
        ]
    }
