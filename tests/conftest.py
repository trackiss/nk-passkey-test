"""Shared fixture definitions."""

import os

import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.virtual_authenticator import VirtualAuthenticatorOptions

import shutil

from nk_passkey_test.common import CREDENTIALS_DIR


@pytest.fixture()
def driver():
    """Create and teardown Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", False)
    d = webdriver.Chrome(options=options)
    yield d
    try:
        d.quit()
    except Exception:
        pass


@pytest.fixture()
def virtual_auth_driver(driver: webdriver.Chrome):
    """Driver with Virtual Authenticator configured."""
    opts = VirtualAuthenticatorOptions(
        protocol="ctap2",
        transport="internal",
        has_resident_key=True,
        has_user_verification=True,
        is_user_consenting=True,
        is_user_verified=True,
    )
    driver.add_virtual_authenticator(opts)
    return driver


@pytest.fixture()
def login_url():
    """Load URL from .env file."""
    load_dotenv()
    url = os.getenv("NK_LOGIN_URL")
    if not url:
        pytest.skip("NK_LOGIN_URL が .env に設定されていません")
    return url


@pytest.fixture()
def clean_credentials():
    """Remove credentials directory before and after test."""
    if CREDENTIALS_DIR.exists():
        shutil.rmtree(CREDENTIALS_DIR)
    yield CREDENTIALS_DIR
    if CREDENTIALS_DIR.exists():
        shutil.rmtree(CREDENTIALS_DIR)
