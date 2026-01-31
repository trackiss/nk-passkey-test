import json
import sys
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.virtual_authenticator import (
    Credential,
    VirtualAuthenticatorOptions,
)
from selenium.webdriver.support.ui import WebDriverWait

CREDENTIALS_DIR = Path("credentials")
LOGIN_TITLE_KEYWORDS = ("ログイン", "二要素認証", "認証")


def load_url() -> str:
    """Load URL from .env file."""
    load_dotenv()
    url = os.getenv("NK_LOGIN_URL")
    if not url:
        print("ERROR: NK_LOGIN_URL が .env ファイルに設定されていません。")
        print("トラブルシュート: .env にログイン URL を設定してください。")
        sys.exit(1)
    return url


def create_driver() -> webdriver.Chrome:
    """Create Chrome WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", False)
    return webdriver.Chrome(options=options)


def setup_virtual_authenticator(driver: webdriver.Chrome) -> None:
    """Set up Virtual Authenticator with CTAP2 + resident key."""
    opts = VirtualAuthenticatorOptions(
        protocol="ctap2",
        transport="internal",
        has_resident_key=True,
        has_user_verification=True,
        is_user_consenting=True,
        is_user_verified=True,
    )
    driver.add_virtual_authenticator(opts)


def wait_for_login(driver: webdriver.Chrome) -> None:
    """Detect login completion using WebDriverWait by monitoring the page title."""
    print("ログインしてください。ログイン完了を自動検知します...")
    WebDriverWait(driver, 300).until(
        lambda d: all(kw not in d.title for kw in LOGIN_TITLE_KEYWORDS)
    )
    print("ログイン完了を検知しました。")


def save_credentials(
    credentials: list[Credential], directory: Path = CREDENTIALS_DIR
) -> Path:
    """Save credentials list to a timestamped JSON file under the directory."""
    directory.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
    path = directory / filename
    data = [c.to_dict() for c in credentials]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


def list_credential_files(directory: Path = CREDENTIALS_DIR) -> list[Path]:
    """Return all credential JSON files in the directory, newest first."""
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"), reverse=True)


def load_credentials_from(path: Path) -> list[Credential]:
    """Load credentials from a specific JSON file."""
    data = json.loads(path.read_text())
    return [Credential.from_dict(d) for d in data]


def load_credentials(directory: Path = CREDENTIALS_DIR) -> list[Credential]:
    """Load credentials from the latest JSON file in the directory."""
    files = list_credential_files(directory)
    if not files:
        msg = f"No credential files found in {directory}"
        raise FileNotFoundError(msg)
    return load_credentials_from(files[0])


def credential_exists(directory: Path = CREDENTIALS_DIR) -> bool:
    """Check if any credential file exists in the directory."""
    return len(list_credential_files(directory)) > 0


def extract_domain(url: str) -> str:
    """Extract the registered domain (without subdomain) from a URL.

    For multi-part TLDs such as .co.jp, .or.jp, .ne.jp, etc.,
    returns the second-level domain (e.g. 'example.co.jp').
    For standard TLDs, returns the last two parts (e.g. 'example.com').
    """
    hostname = urlparse(url).hostname
    if hostname is None:
        msg = f"Invalid URL: {url}"
        raise ValueError(msg)
    parts = hostname.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "or", "ne", "ac", "go"):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def wait_for_enter(message: str = "Enter を押して続行...") -> None:
    """Display message and wait for Enter key."""
    input(message)


def cleanup_driver(driver: webdriver.Chrome | None) -> None:
    """Safely quit the driver."""
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass


def print_error(error: Exception, tips: list[str] | None = None) -> None:
    """Print error information with troubleshooting tips."""
    print(f"\nERROR: {type(error).__name__}: {error}")
    if tips:
        print("\nトラブルシュート:")
        for tip in tips:
            print(f"  - {tip}")
