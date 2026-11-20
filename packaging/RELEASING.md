# Release & Code-Signing Guide (Maintainers)

This document explains how to build, sign, notarize, and publish desktop installers for **REALM Engine** safely — both locally on macOS and automatically across **macOS (Apple Silicon + Intel)** and **Windows (x64)** via GitHub Actions.

---

## 1. Local macOS Signed & Notarized Build (One-Time Setup)

1. Install a **Developer ID Application** certificate in your macOS `login` Keychain (from [developer.apple.com/account](https://developer.apple.com/account) → *Certificates*).
   Verify it appears as valid:
   ```bash
   security find-identity -v -p codesigning
   ```
2. Create an **App Store Connect API Key** (*Users & Access → Integrations → App Store Connect API*, role **Developer**) and save your `notarytool` profile once in Keychain:
   ```bash
   xcrun notarytool store-credentials "realm-notary" \
     --key /path/to/AuthKey_XXXXXXXXXX.p8 \
     --key-id XXXXXXXXXX \
     --issuer XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
   ```
3. Build, smoke-test (pre-sign & post-sign Hardened Runtime), sign, notarize, staple, and Gatekeeper-verify in one command:
   ```bash
   ./packaging/build_macos.sh --auto-sign --require-signed --notarize-profile "realm-notary"
   ```
   Output on Apple Silicon: `dist/REALM-Engine-<version>-macos-apple-silicon.dmg`.
   Output on Intel Mac: `dist/REALM-Engine-<version>-macos-intel.dmg`.

---

## 2. Automated Multi-OS GitHub Releases (macOS Apple Silicon + macOS Intel + Windows x64)

The release workflow [`.github/workflows/release.yml`](../.github/workflows/release.yml) runs automatically whenever you push a tag matching `v*.*.*` (and checks that the tag matches `project.version` in `pyproject.toml`).

### Configuring Apple Signing & Notarization Secrets in GitHub (Recommended)

Without these secrets, `release.yml` creates a **Draft** release so unsigned macOS DMGs are never accidentally published as final. To enable automatic Developer ID signing + Apple notarization for **both Apple Silicon and Intel Macs**:

1. **Export your Developer ID Application certificate from Keychain Access:**
   - Open **Keychain Access → `login` → My Certificates**.
   - Right-click **`Developer ID Application: ...`** → **Export** → save as `DeveloperID.p12` with a strong export password.
2. **Base64-encode the `.p12` and your App Store Connect `.p8` key** (copy straight to clipboard without writing plaintext to the repo):
   ```bash
   base64 -i DeveloperID.p12 | pbcopy
   base64 -i AuthKey_XXXXXXXXXX.p8 | pbcopy
   ```
   *(Delete temporary `.p12` exports from disk afterward.)*
3. **Add 5 Repository Secrets** in GitHub under **Settings → Secrets and variables → Actions → New repository secret**:

| Secret Name | Value |
|---|---|
| `MACOS_CERT_P12_BASE64` | Base64 output of `DeveloperID.p12` |
| `MACOS_CERT_PASSWORD` | Password used when exporting `DeveloperID.p12` |
| `APPLE_ASC_KEY_P8_BASE64` | Base64 output of `AuthKey_XXXXXXXXXX.p8` |
| `APPLE_ASC_KEY_ID` | 10-character Key ID (e.g. `AB12CD34EF`) |
| `APPLE_ASC_ISSUER_ID` | App Store Connect Issuer UUID |

During CI runs, credentials are imported into an ephemeral `$RUNNER_TEMP` Keychain and deleted unconditionally in an `if: always()` cleanup step.

---

## 3. Cutting a New Release

1. Update `version` in `pyproject.toml` and refresh `uv.lock`:
   ```bash
   uv lock
   ```
2. Run the full verification gate locally:
   ```bash
   uv run ruff check . && uv run pyright && uv run pytest
   ```
3. Commit on `main`, tag the exact matching version, and push:
   ```bash
   git tag -a v0.2.0 -m "REALM Engine v0.2.0"
   git push origin main --follow-tags
   ```
4. Watch **GitHub → Actions → Release Desktop Installers** complete. It will verify tests, build & smoke-test all 3 platforms, generate `SHA256SUMS.txt`, and create the GitHub Release.
