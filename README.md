# nk-passkey-test

## requirements

- Python 3.13+
- Google Chrome

---

## for Windows users

### setup

```powershell
$URL = "login URL here"
Add-Content -Path .env -Value "NK_LOGIN_URL=$URL"

# Python (venv)
python -m venv .venv
.venv\Scripts\Activate.ps1

# uv
uv sync
```

### register passkey

```powershell
# Python (venv)
register

# uv
uv run register
```

### login with passkey

```powershell
# Python (venv)
login

# uv
uv run login
```

### deactivate venv

```powershell
# Python (venv)
deactivate
```

---

## for Mac/Linux users

### setup

```bash
URL='login URL here'
echo "NK_LOGIN_URL=$URL" > .env

# Python (venv)
python -m venv .venv
source .venv/bin/activate

# uv
uv sync
```

### register passkey

```bash
# Python (venv)
register

# uv
uv run register
```

### login with passkey

```bash
# Python (venv)
login

# uv
uv run login
```

### deactivate venv

```bash
# Python (venv)
deactivate
```

---

## integration test

```bash
# Python (venv)
pytest tests/test_integration.py -v -s

# uv
uv run pytest tests/test_integration.py -v -s
```
