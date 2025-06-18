import tempfile
import shutil
import subprocess
import pytest
import os


def pytest_addoption(parser):
    parser.addoption(
        "--test-images",
        action="store_true",
        default=False,
        help="Run tests that use image comparison with reference images.",
    )


@pytest.fixture(scope="session")
def mpl_image_compare_setup(request):
    if not request.config.getoption("--test-images"):
        pytest.skip("Skipping image comparison tests because --test-images not set")

    temp_dir = tempfile.mkdtemp()
    repo_url = "https://github.com/ecmwf/earthkit-plots-test-images.git"
    
    try:
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)
