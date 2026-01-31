"""Login using passkey script."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from nk_passkey_test.common import (
    LOGIN_TITLE_KEYWORDS,
    create_driver,
    list_credential_files,
    load_credentials_from,
    load_url,
    print_error,
    save_credentials_to,
    setup_virtual_authenticator,
    wait_for_enter,
)

SELECTOR_PASSKEY_LOGIN = "button.pskey-submit__button_type"  # Passkey login button

WAIT_TIMEOUT = 30  # Element wait timeout (seconds)
LOGIN_DETECT_TIMEOUT = 60  # Login success detection timeout (seconds)


def main() -> None:
    try:
        # 1. List credential files and let user choose
        files = list_credential_files()
        if not files:
            print(
                "クレデンシャルがまだありません。先に register.py を実行してください。"
            )
            wait_for_enter("Enter を押して終了...")
            return

        if len(files) == 1:
            selected = files[0]
        else:
            print("使用するクレデンシャルを選択してください:")
            for i, f in enumerate(files, 1):
                print(f"  {i}) {f.name}")
            while True:
                choice = input(f"番号を入力 [1-{len(files)}]: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(files):
                    selected = files[int(choice) - 1]
                    break
                print("無効な入力です。もう一度入力してください。")

        # 2. Launch browser + set up Virtual Authenticator
        url = load_url()
        driver = create_driver()
        setup_virtual_authenticator(driver)

        # 3. Load credentials + add them
        credentials = load_credentials_from(selected)
        for cred in credentials:
            driver.add_credential(cred)
        print(
            f"クレデンシャルを {len(credentials)} 件読み込みました。({selected.name})"
        )

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

        # 7. Update credentials (signCount) for next login
        updated = driver.get_credentials()
        if updated:
            save_credentials_to(updated, selected)
            print("クレデンシャルを更新しました。(signCount 同期)")

        # 8. Success message
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
