"""Register passkey script."""

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from nk_passkey_test.common import (
    create_driver,
    load_url,
    print_error,
    save_credentials,
    setup_virtual_authenticator,
    wait_for_enter,
    wait_for_login,
)

# Direct link to passkey setup (if present in header)
SELECTOR_PASSKEY_SETUP = 'a[href*="/kyak/passkey_settei/init"]'

# Fallback: Account Info header link → Passkey setup link in Account Info page
SELECTOR_ACCOUNT_INFO_HEADER = 'img[alt="口座情報"]'

WAIT_TIMEOUT = 30  # Element wait timeout (seconds)
SHORT_TIMEOUT = 5  # Short timeout (for fallback detection)


def navigate_to_passkey_setup(driver: webdriver.Chrome) -> None:
    """Navigate to the passkey setup page."""
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    short_wait = WebDriverWait(driver, SHORT_TIMEOUT)

    # Strategy 1: Try to find the passkey setup link on the current page
    print("パスキー設定リンクを探しています...")
    try:
        passkey_link = short_wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_PASSKEY_SETUP))
        )
        print("パスキー設定リンクを発見しました。クリックします...")
        passkey_link.click()
        return
    except TimeoutException:
        print("直接リンクが見つかりません。口座情報経由で遷移します...")

    # Strategy 2: Via Account Info header link
    print("ヘッダーの「口座情報」ボタンを探しています...")
    account_info_img = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_ACCOUNT_INFO_HEADER))
    )
    # Click the parent a tag of the img element
    account_info_link = account_info_img.find_element(By.XPATH, "./..")
    account_info_link.click()

    print("口座情報ページで「パスキー設定」リンクを探しています...")
    passkey_link = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_PASSKEY_SETUP))
    )
    passkey_link.click()


def main() -> None:
    try:
        # 1. Launch browser + set up Virtual Authenticator
        url = load_url()
        driver = create_driver()
        setup_virtual_authenticator(driver)

        # 3. Access the URL
        print(f"ページにアクセスしています: {url}")
        driver.get(url)

        # 4. Detect automatic transition after login
        wait_for_login(driver)

        # 5. Confirm login success (based on title)
        print(f"ログイン後のURL: {driver.current_url}")
        print(f"ページタイトル: {driver.title}")

        # 6. Automatic navigation to passkey setup page (with fallback)
        navigate_to_passkey_setup(driver)

        # 7. Click the OTP send button
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        print("「ワンタイムパスワードを送信する」ボタンをクリックします...")
        otp_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'input[alt="ワンタイムパスワードを送信する"]')
            )
        )
        otp_button.click()

        # 8. Delegate OTP input to the user
        #    Wait for transition to passkey setup page after OTP input and authentication completion
        #    The page title remains "Passkey Setup", then proceed to step 2
        print("\n" + "=" * 60)
        print("OTP（ワンタイムパスワード）がメールで届きます。")
        print("ブラウザで OTP を入力し、本人認証を完了してください。")
        print("パスキー設定画面が表示されるまで自動で待機します...")
        print("=" * 60 + "\n")

        # Wait for OTP input completion (Step 2 = Detect transition to passkey setup confirmation page)
        print("OTP 入力完了を待機中...")
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'img[src*="step_passkey_settei_02_on"]')
            )
        )
        print("OTP 認証が完了しました。")

        # 9. Wait for manual click of "Set up Passkey" button
        print("\n" + "=" * 60)
        print("ブラウザで「パスキーを設定する」ボタンを押してください。")
        print("Virtual Authenticator が自動応答し、設定完了を待機します...")
        print("=" * 60 + "\n")

        # 10. Wait for WebAuthn ceremony completion
        # Button press → JS communicates with FIDO server → navigator.credentials.create()
        # → Virtual Authenticator automatically responds → Transition to step 3 (setup complete)
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'img[src*="step_passkey_settei_03_on"]')
            )
        )
        print("パスキー設定が完了しました！")

        # 11. Retrieve and save credentials
        credentials = driver.get_credentials()
        if not credentials:
            raise RuntimeError(
                "パスキー登録に失敗しました。クレデンシャルが取得できません。"
            )
        print(f"取得したクレデンシャル数: {len(credentials)}")
        saved_path = save_credentials(credentials)
        print(f"クレデンシャルを保存しました: {saved_path}")

        # 12. Success message
        print("\nパスキー登録に成功しました。")
        wait_for_enter("Enter を押して終了...")

    except KeyboardInterrupt:
        print("\nユーザーにより中断されました。")
    except Exception as e:
        print_error(
            e,
            tips=[
                "Chrome がインストールされているか確認してください",
                "ChromeDriver のバージョンが Chrome と一致しているか確認してください",
                "ログイン後に正しい画面に遷移しているか確認してください",
                ".env ファイルに URL が設定されているか確認してください",
            ],
        )


if __name__ == "__main__":
    main()
