from app import repo_file_url


def test_github_https():
    url = repo_file_url("https://github.com/org/repo.git", "src/main.py")
    assert url == "https://github.com/org/repo/blob/HEAD/src/main.py"


def test_github_https_no_git_suffix():
    url = repo_file_url("https://github.com/org/repo", "README.md")
    assert url == "https://github.com/org/repo/blob/HEAD/README.md"


def test_github_ssh():
    url = repo_file_url("git@github.com:org/repo.git", "Dockerfile")
    assert url == "https://github.com/org/repo/blob/HEAD/Dockerfile"


def test_gitlab_https():
    url = repo_file_url("https://gitlab.com/group/project.git", "ci.yml")
    assert url == "https://gitlab.com/group/project/-/blob/HEAD/ci.yml"


def test_bitbucket_https():
    url = repo_file_url("https://bitbucket.org/team/repo.git", "setup.py")
    assert url == "https://bitbucket.org/team/repo/src/HEAD/setup.py"


def test_other_host():
    url = repo_file_url("https://gitea.example.com/org/repo.git", "main.go")
    assert url == "https://gitea.example.com/org/repo/blob/HEAD/main.go"


def test_none_inputs():
    assert repo_file_url(None, "file.py") is None
    assert repo_file_url("https://github.com/org/repo", None) is None
    assert repo_file_url("", "file.py") is None
    assert repo_file_url("https://github.com/org/repo", "") is None
