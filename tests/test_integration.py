"""Integration test: register → login sequential execution."""

import json

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from nk_passkey_test.common import (
    LOGIN_TITLE_KEYWORDS,
    credential_exists,
    extract_domain,
    load_credentials,
    save_credentials,
)
from nk_passkey_test.login import LOGIN_DETECT_TIMEOUT, SELECTOR_PASSKEY_LOGIN
from nk_passkey_test.register import (
    SELECTOR_ACCOUNT_INFO_HEADER,
    SELECTOR_PASSKEY_SETUP,
    SHORT_TIMEOUT,
    WAIT_TIMEOUT,
)

HUMAN_TIMEOUT = 300


class TestPasskeyIntegration:
    """Verify the complete register → login flow."""

    def test_register_and_login(
        self,
        virtual_auth_driver,
        login_url: str,
        clean_credentials,
    ) -> None:
        """Verify the complete register → login flow."""
        driver = virtual_auth_driver

        # ==================== Phase 1: Register ====================
        print("\n===== Phase 1: Register =====")

        # 1. Verify no credentials exist
        assert not credential_exists(), "クレデンシャルが既に存在します"

        # 2. Access login page
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

        # ==================== Phase 2: Login ====================
        print("\n===== Phase 2: Login =====")

        # 1. Verify credentials exist
        assert credential_exists(), "クレデンシャルが存在しません"

        # 2. Launch new browser + configure Virtual Authenticator
        from selenium import webdriver as wd
        from selenium.webdriver.common.virtual_authenticator import (
            VirtualAuthenticatorOptions,
        )

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

            # 3. Load credentials and inject
            creds = load_credentials()
            for cred in creds:
                login_driver.add_credential(cred)
            print(f"クレデンシャルを {len(creds)} 件読み込みました。")

            # 4. Access login page
            print(f"ページにアクセスしています: {login_url}")
            login_driver.get(login_url)

            # 5. Click passkey login button
            login_wait = WebDriverWait(login_driver, WAIT_TIMEOUT)
            print("パスキーログインボタンを探しています...")
            passkey_login_btn = login_wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_PASSKEY_LOGIN))
            )
            passkey_login_btn.click()
            print("パスキーログインを実行中...")

            # 6. Wait for login success (automatic, 60 seconds)
            WebDriverWait(login_driver, LOGIN_DETECT_TIMEOUT).until(
                lambda d: all(kw not in d.title for kw in LOGIN_TITLE_KEYWORDS)
            )
            page_title = login_driver.title
            print(f"ログイン後のページタイトル: {page_title}")

            # 7. Login assertions
            for kw in LOGIN_TITLE_KEYWORDS:
                assert kw not in page_title, (
                    f"ページタイトルに '{kw}' が含まれています: {page_title}"
                )
            print("Phase 2 (Login) 完了")

        finally:
            try:
                login_driver.quit()
            except Exception:
                pass
