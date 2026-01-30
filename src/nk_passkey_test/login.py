"""Login using passkey script."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from nk_passkey_test.common import (
    LOGIN_TITLE_KEYWORDS,
    create_driver,
    credential_exists,
    load_credentials,
    load_url,
    print_error,
    setup_virtual_authenticator,
    wait_for_enter,
)

SELECTOR_PASSKEY_LOGIN = "button.pskey-submit__button_type"  # Passkey login button

WAIT_TIMEOUT = 30  # Element wait timeout (seconds)
LOGIN_DETECT_TIMEOUT = 60  # Login success detection timeout (seconds)


def main() -> None:
    try:
        # 1. Check if credentials exist
        if not credential_exists():
            print(
                "クレデンシャルがまだありません。先に register.py を実行してください。"
            )
            wait_for_enter("Enter を押して終了...")
            return

        # 2. Launch browser + set up Virtual Authenticator
        url = load_url()
        driver = create_driver()
        setup_virtual_authenticator(driver)

        # 3. Load credentials + add them
        credentials = load_credentials()
        for cred in credentials:
            driver.add_credential(cred)
        print(f"クレデンシャルを {len(credentials)} 件読み込みました。")

        # 4. Access the URL
        print(f"ページにアクセスしています: {url}")
        driver.get(url)

        # 5. Click the Passkey login button
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        print("パスキーログインボタンを探しています...")
        passkey_login_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_PASSKEY_LOGIN))
        )
        passkey_login_btn.click()
        print("パスキーログインを実行中... (Virtual Authenticator が自動応答します)")

        # 6. Confirm login success (based on title)
        WebDriverWait(driver, LOGIN_DETECT_TIMEOUT).until(
            lambda d: all(kw not in d.title for kw in LOGIN_TITLE_KEYWORDS)
        )
        print(f"ログイン後のURL: {driver.current_url}")
        print(f"ページタイトル: {driver.title}")

        # 7. Success message
        print("\nパスキーログインに成功しました。")
        wait_for_enter("Enter を押して終了...")

    except KeyboardInterrupt:
        print("\nユーザーにより中断されました。")
    except Exception as e:
        print_error(
            e,
            tips=[
                "クレデンシャルが正しい形式か確認してください",
                "パスキーが正常に登録されているか確認してください",
                "Chrome と ChromeDriver のバージョンが一致しているか確認してください",
                ".env ファイルに URL が設定されているか確認してください",
            ],
        )


if __name__ == "__main__":
    main()
