import nox

nox.options.reuse_existing_virtualenvs = True

@nox.session
def ruff(session):
    """Lint and fix what is fixable"""
    session.install('ruff')
    session.run(
        'ruff',
        'check',
        '--force-exclude',
        '--fix',
        '--show-fixes',
        "."
    ) # TODO make this a pre-commit hook at some point

@nox.session
def test(session):
    """Run the testsuite."""
    session.install('.', 'pytest', 'pytest-cov')
    session.run(
        'pytest',
        #"--cov=adbdevice",
        #"--cov-config", "pyproject.toml",
        #"--cov-report", "html",
        "tests"
    )

