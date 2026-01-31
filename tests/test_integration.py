"""Integration test: register → login sequential execution."""

import json
from pathlib import Path

from selenium import webdriver as wd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.virtual_authenticator import VirtualAuthenticatorOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from nk_passkey_test.common import (
    LOGIN_TITLE_KEYWORDS,
    credential_exists,
    extract_domain,
    load_credentials_from,
    save_credentials,
    save_credentials_to,
)
from nk_passkey_test.login import LOGIN_DETECT_TIMEOUT, SELECTOR_PASSKEY_LOGIN
from nk_passkey_test.register import (
    SELECTOR_ACCOUNT_INFO_HEADER,
    SELECTOR_PASSKEY_SETUP,
    SHORT_TIMEOUT,
    WAIT_TIMEOUT,
)

HUMAN_TIMEOUT = 300


def _do_passkey_login(login_url: str, cred_file: Path) -> list[dict]:
    """Perform a single passkey login and return updated credential dicts.

    Launches a fresh browser, loads credentials from the given file,
    performs passkey login, updates the credential file with the new
    signCount, and returns the raw credential dicts after login.
    """
    options = wd.ChromeOptions()
    options.add_experimental_option("detach", False)
    login_driver = wd.Chrome(options=options)

    try:
        va_opts = VirtualAuthenticatorOptions(
            protocol="ctap2",
            transport="internal",
            has_resident_key=True,
            has_user_verification=True,
            is_user_consenting=True,
            is_user_verified=True,
        )
        login_driver.add_virtual_authenticator(va_opts)

        # Load credentials and inject
        creds = load_credentials_from(cred_file)
        for cred in creds:
            login_driver.add_credential(cred)
        print(f"クレデンシャルを {len(creds)} 件読み込みました。")

        # Access login page
        print(f"ページにアクセスしています: {login_url}")
        login_driver.get(login_url)

        # Click passkey login button
        login_wait = WebDriverWait(login_driver, WAIT_TIMEOUT)
        print("パスキーログインボタンを探しています...")
        passkey_login_btn = login_wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_PASSKEY_LOGIN))
        )
        passkey_login_btn.click()
        print("パスキーログインを実行中...")

        # Wait for login success
        WebDriverWait(login_driver, LOGIN_DETECT_TIMEOUT).until(
            lambda d: all(kw not in d.title for kw in LOGIN_TITLE_KEYWORDS)
        )
        page_title = login_driver.title
        print(f"ログイン後のページタイトル: {page_title}")

        for kw in LOGIN_TITLE_KEYWORDS:
            assert kw not in page_title, (
                f"ページタイトルに '{kw}' が含まれています: {page_title}"
            )

        # Save updated credentials (signCount synced)
        updated = login_driver.get_credentials()
        if updated:
            save_credentials_to(updated, cred_file)

        # Return raw dicts for signCount inspection
        return json.loads(cred_file.read_text())

    finally:
        try:
            login_driver.quit()
        except Exception:
            pass


class TestPasskeyIntegration:
    """Verify the complete register → login flow."""

    def test_register_and_login(
        self,
        virtual_auth_driver,
        login_url: str,
    ) -> None:
        """Verify the complete register → login flow."""
        driver = virtual_auth_driver

        # ==================== Phase 1: Register ====================
        print("\n===== Phase 1: Register =====")

        # 1. Access login page
        print(f"ページにアクセスしています: {login_url}")
        driver.get(login_url)

        # 3. Wait for login completion (human operation, 300 seconds)
        print("ログインしてください。ログイン完了を自動検知します...")
        WebDriverWait(driver, HUMAN_TIMEOUT).until(
            lambda d: all(kw not in d.title for kw in LOGIN_TITLE_KEYWORDS)
        )
        print(f"ログイン完了を検知しました。タイトル: {driver.title}")

        # 4. Click passkey setup link (with fallback)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        short_wait = WebDriverWait(driver, SHORT_TIMEOUT)

        print("パスキー設定リンクを探しています...")
        try:
            passkey_link = short_wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_PASSKEY_SETUP))
            )
            print("パスキー設定リンクを発見しました。クリックします...")
            passkey_link.click()
        except Exception:
            print("直接リンクが見つかりません。口座情報経由で遷移します...")
            account_info_img = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, SELECTOR_ACCOUNT_INFO_HEADER)
                )
            )
            account_info_link = account_info_img.find_element(By.XPATH, "./..")
            account_info_link.click()

            print("口座情報ページで「パスキー設定」リンクを探しています...")
            passkey_link = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_PASSKEY_SETUP))
            )
            passkey_link.click()

        # 5. Automatically click OTP send button
        print("「ワンタイムパスワードを送信する」ボタンをクリックします...")
        otp_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'input[alt="ワンタイムパスワードを送信する"]')
            )
        )
        otp_button.click()

        # 6. Wait for OTP input completion (human operation, 300 seconds)
        print("\n" + "=" * 60)
        print("OTP（ワンタイムパスワード）がメールで届きます。")
        print("ブラウザで OTP を入力し、本人認証を完了してください。")
        print("=" * 60 + "\n")

        print("OTP 入力完了を待機中...")
        WebDriverWait(driver, HUMAN_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'img[src*="step_passkey_settei_02_on"]')
            )
        )
        print("OTP 認証が完了しました。")

        # 7. Wait for "Set up Passkey" button click (human operation, 300 seconds)
        print("\n" + "=" * 60)
        print("ブラウザで「パスキーを設定する」ボタンを押してください。")
        print("Virtual Authenticator が自動応答します。")
        print("=" * 60 + "\n")

        WebDriverWait(driver, HUMAN_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'img[src*="step_passkey_settei_03_on"]')
            )
        )
        print("パスキー設定が完了しました！")

        # 8. Retrieve and save credentials
        credentials = driver.get_credentials()
        assert len(credentials) >= 1, "クレデンシャルが取得できません"

        saved_path = save_credentials(credentials)
        print(f"取得したクレデンシャル数: {len(credentials)}")

        # 9. Register assertions
        assert credential_exists(), "クレデンシャルが保存されていません"

        saved_data = json.loads(saved_path.read_text())
        assert len(saved_data) >= 1, "保存されたクレデンシャルが空です"
        expected_domain = extract_domain(login_url)
        assert saved_data[0]["rpId"] == expected_domain, (
            f"rpId が期待値と異なります: {saved_data[0].get('rpId')}"
        )

        # 10. Phase 1 complete → close browser
        print("Phase 1 (Register) 完了")
        try:
            driver.quit()
        except Exception:
            pass

        # ==================== Phase 2: Login (1st) ====================
        print("\n===== Phase 2: Login (1st) =====")
        assert credential_exists(), "クレデンシャルが存在しません"

        data_after_login1 = _do_passkey_login(login_url, saved_path)
        sign_count_1 = data_after_login1[0]["signCount"]
        print(f"1回目ログイン後の signCount: {sign_count_1}")
        print("Phase 2 (Login 1st) 完了")

        # ==================== Phase 3: Login (2nd) ====================
        print("\n===== Phase 3: Login (2nd) =====")

        data_after_login2 = _do_passkey_login(login_url, saved_path)
        sign_count_2 = data_after_login2[0]["signCount"]
        print(f"2回目ログイン後の signCount: {sign_count_2}")

        assert sign_count_2 > sign_count_1, (
            f"signCount が増加していません: {sign_count_1} → {sign_count_2}"
        )
        print("Phase 3 (Login 2nd) 完了 — signCount 増加を確認")
