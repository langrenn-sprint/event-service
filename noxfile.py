"""Nox sessions."""
import tempfile

import nox
from nox_poetry import Session, session

package = "event_service"
locations = "src", "tests", "noxfile.py"
nox.options.envdir = ".cache"
nox.options.reuse_existing_virtualenvs = True
nox.options.stop_on_first_error = True
nox.options.sessions = (
    "lint",
    "mypy",
    "pytype",
    "unit_tests",
    "integration_tests",
    "contract_tests",
)


@session
def unit_tests(session: Session) -> None:
    """Run the unit test suite."""
    args = session.posargs
    session.install(".")
    session.install(
        "pytest",
        "pytest-mock",
        "pytest-aiohttp",
        "requests",
        "aioresponses",
    )
    session.run(
        "pytest",
        "-m unit",
        "-rA",
        *args,
        env={"CONFIG": "test", "JWT_SECRET": "secret"},
    )


@session
def integration_tests(session: Session) -> None:
    """Run the integration test suite."""
    args = session.posargs or ["--cov"]
    session.install(".")
    session.install(
        "coverage[toml]",
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "pytest-aiohttp",
        "requests",
        "aioresponses",
    )
    session.run(
        "pytest",
        "-m integration",
        "-rF",
        *args,
        env={
            "CONFIG": "test",
            "JWT_SECRET": "secret",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "password",
            "USERS_HOST_SERVER": "example.com",
            "USERS_HOST_PORT": "8081",
        },
    )


@session
def contract_tests(session: Session) -> None:
    """Run the contract test suite."""
    args = session.posargs
    session.install(".")
    session.install(
        "pytest",
        "pytest-docker",
        "pytest_mock",
        "pytest-asyncio",
        "requests",
        "aioresponses",
    )
    session.run(
        "pytest",
        "-m contract",
        "-rA",
        *args,
        env={
            "CONFIG": "test",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "password",
            "USERS_HOST_SERVER": "localhost",
            "USERS_HOST_PORT": "8081",
            "JWT_EXP_DELTA_SECONDS": "60",
            "DB_USER": "event-service",
            "DB_PASSWORD": "password",
            "LOGGING_LEVEL": "DEBUG",
        },
    )


@session
def black(session: Session) -> None:
    """Run black code formatter."""
    args = session.posargs or locations
    session.install("black")
    session.run("black", *args)


@session
def lint(session: Session) -> None:
    """Lint using flake8."""
    args = session.posargs or locations
    session.install(
        "flake8",
        "flake8-annotations",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-import-order",
        "darglint",
        "flake8-assertive",
        "flake8-eradicate",
    )
    session.run("flake8", *args)


@session
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            "--without-hashes",
            f"--output={requirements.name}",
            external=True,
        )
        session.install("safety")
        session.run("safety", "check", f"--file={requirements.name}", "--full-report")


@session
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or locations
    session.install("mypy")
    session.run("mypy", *args)


@session
def pytype(session: Session) -> None:
    """Run the static type checker using pytype."""
    args = session.posargs or ["--disable=import-error", *locations]
    session.install("pytype")
    session.run("pytype", *args)


@session
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.install(".")
    session.install("xdoctest")
    session.run("python", "-m", "xdoctest", package, *args)


@session
def docs(session: Session) -> None:
    """Build the documentation."""
    session.install(".")
    session.install("sphinx", "sphinx_autodoc_typehints")
    session.run("sphinx-build", "docs", "docs/_build")


@session
def coverage(session: Session) -> None:
    """Upload coverage data."""
    session.install("coverage[toml]", "codecov")
    session.run("coverage", "xml", "--fail-under=0")
    session.run("codecov", *session.posargs)
