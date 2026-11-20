#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SIGN_IDENTITY=""
AUTO_SIGN=0
REQUIRE_SIGNED=0
NOTARIZE_PROFILE=""
NOTARY_KEY=""
NOTARY_KEY_ID=""
NOTARY_ISSUER=""
SKIP_DMG=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sign)
      SIGN_IDENTITY="${2:?Missing signing identity after --sign}"
      shift 2
      ;;
    --auto-sign)
      AUTO_SIGN=1
      shift
      ;;
    --require-signed)
      REQUIRE_SIGNED=1
      shift
      ;;
    --notarize-profile)
      NOTARIZE_PROFILE="${2:?Missing keychain profile name after --notarize-profile}"
      shift 2
      ;;
    --notary-key)
      NOTARY_KEY="${2:?Missing .p8 key path after --notary-key}"
      shift 2
      ;;
    --notary-key-id)
      NOTARY_KEY_ID="${2:?Missing key ID after --notary-key-id}"
      shift 2
      ;;
    --notary-issuer)
      NOTARY_ISSUER="${2:?Missing issuer UUID after --notary-issuer}"
      shift 2
      ;;
    --skip-dmg)
      SKIP_DMG=1
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--sign \"Developer ID Application: ...\"] [--auto-sign] [--require-signed] [--notarize-profile <profile> | --notary-key <p8> --notary-key-id <id> --notary-issuer <uuid>] [--skip-dmg]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

VERSION="$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml","rb"))["project"]["version"])')"
RAW_ARCH="$(uname -m)"
case "$RAW_ARCH" in
  arm64) ARCH_LABEL="apple-silicon" ;;
  x86_64) ARCH_LABEL="intel" ;;
  *) ARCH_LABEL="$RAW_ARCH" ;;
esac

VOL_NAME="REALM Engine"
APP_BUNDLE="$ROOT/dist/REALM Engine.app"
DMG_PATH="$ROOT/dist/REALM-Engine-${VERSION}-macos-${ARCH_LABEL}.dmg"
ENTITLEMENTS="$ROOT/packaging/entitlements.plist"
ICON_SRC="$ROOT/features/ui/static/logo-512.png"
ICON_DIR="$ROOT/packaging/icons"
ICONSET="$ICON_DIR/realm-engine.iconset"
ICNS="$ICON_DIR/realm-engine.icns"

echo "==> Generating macOS .icns icon from $ICON_SRC"
rm -rf "$ICONSET"
mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" "$ICON_SRC" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  double=$((size * 2))
  sips -z "$double" "$double" "$ICON_SRC" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$ICNS"
rm -rf "$ICONSET"

echo "==> Building REALM Engine.app (${VERSION}, ${ARCH_LABEL} / ${RAW_ARCH}) with PyInstaller"
uv run --group desktop pyinstaller --noconfirm --clean "$ROOT/packaging/realm-engine.spec"

run_smoke_test() {
  local smoke_dir
  smoke_dir="$(mktemp -d "${TMPDIR:-/tmp}/realm-smoke.XXXXXX")"
  "$APP_BUNDLE/Contents/MacOS/REALM Engine" --smoke-test --data-dir "$smoke_dir"
  test -f "$smoke_dir/knowledge_base/welcome.md"
  rm -rf "$smoke_dir"
}

echo "==> Running headless smoke test on built app bundle"
run_smoke_test
echo "    Smoke test passed (server, /healthz, /, /static/ui.css, WebView backend, starter vault)"

if [[ "$AUTO_SIGN" -eq 1 && -z "$SIGN_IDENTITY" ]]; then
  SIGN_IDENTITY="$(security find-identity -v -p codesigning | sed -n 's/.*"\(Developer ID Application: [^"]*\)".*/\1/p' | head -n 1 || true)"
  if [[ -z "$SIGN_IDENTITY" ]]; then
    if [[ "$REQUIRE_SIGNED" -eq 1 ]]; then
      echo "Error: --require-signed was specified, but no 'Developer ID Application' certificate was found in Keychain." >&2
      exit 1
    fi
    echo "    Note: No 'Developer ID Application' certificate found in Keychain; leaving bundle ad-hoc signed."
  fi
fi

if [[ "$REQUIRE_SIGNED" -eq 1 && -z "$SIGN_IDENTITY" ]]; then
  echo "Error: --require-signed requires --sign or --auto-sign with an installed Developer ID Application certificate." >&2
  exit 1
fi

if [[ -n "$SIGN_IDENTITY" ]]; then
  echo "==> Code-signing bundle with: $SIGN_IDENTITY"
  # Sign nested Mach-O binaries bottom-up for Apple Notary compliance (avoiding deprecated --deep)
  find "$APP_BUNDLE/Contents" -type f \( -name "*.dylib" -o -name "*.so" -o -perm -111 \) ! -path "$APP_BUNDLE/Contents/MacOS/REALM Engine" -print0 \
    | while IFS= read -r -d '' bin; do
        if file "$bin" | grep -q "Mach-O"; then
          codesign --force --options runtime --timestamp --entitlements "$ENTITLEMENTS" --sign "$SIGN_IDENTITY" "$bin"
        fi
      done
  codesign --force --options runtime --timestamp --entitlements "$ENTITLEMENTS" --sign "$SIGN_IDENTITY" "$APP_BUNDLE/Contents/MacOS/REALM Engine"
  codesign --force --options runtime --timestamp --entitlements "$ENTITLEMENTS" --sign "$SIGN_IDENTITY" "$APP_BUNDLE"
  codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE"
  echo "==> Re-running smoke test under Hardened Runtime"
  run_smoke_test
  echo "    Post-sign Hardened Runtime smoke test passed"
fi

if [[ "$SKIP_DMG" -eq 0 ]]; then
  echo "==> Creating styled drag-to-Applications DMG: $DMG_PATH"
  BG_PNG="$ICON_DIR/installer-bg.png"
  uv run --group desktop python "$ROOT/packaging/make_dmg_background.py" "$BG_PNG"

  if [[ -d "/Volumes/$VOL_NAME" ]]; then
    hdiutil detach "/Volumes/$VOL_NAME" -force >/dev/null 2>&1 || true
  fi

  rm -f "$DMG_PATH"
  REALM_DMG_APP="$APP_BUNDLE" \
  REALM_DMG_BG="$BG_PNG" \
  REALM_DMG_ICON="$ICNS" \
  uv run --group desktop dmgbuild -s "$ROOT/packaging/dmg_settings.py" "$VOL_NAME" "$DMG_PATH"

  if [[ -n "$SIGN_IDENTITY" ]]; then
    codesign --force --timestamp --sign "$SIGN_IDENTITY" "$DMG_PATH"
  fi

  NOTARY_ARGS=()
  if [[ -n "$NOTARIZE_PROFILE" ]]; then
    NOTARY_ARGS=(--keychain-profile "$NOTARIZE_PROFILE")
  elif [[ -n "$NOTARY_KEY" || -n "$NOTARY_KEY_ID" || -n "$NOTARY_ISSUER" ]]; then
    if [[ -z "$NOTARY_KEY" || -z "$NOTARY_KEY_ID" || -z "$NOTARY_ISSUER" ]]; then
      echo "Error: --notary-key, --notary-key-id, and --notary-issuer must all be set together." >&2
      exit 1
    fi
    NOTARY_ARGS=(--key "$NOTARY_KEY" --key-id "$NOTARY_KEY_ID" --issuer "$NOTARY_ISSUER")
  fi

  if [[ ${#NOTARY_ARGS[@]} -gt 0 ]]; then
    if [[ -z "$SIGN_IDENTITY" ]]; then
      echo "Error: Notarization requires --sign or --auto-sign with a Developer ID Application certificate." >&2
      exit 1
    fi
    echo "==> Submitting DMG to Apple Notary Service"
    xcrun notarytool submit "$DMG_PATH" "${NOTARY_ARGS[@]}" --wait
    echo "==> Stapling & validating notarization ticket on DMG"
    xcrun stapler staple "$DMG_PATH"
    xcrun stapler validate "$DMG_PATH"
    spctl --assess --type open --context context:primary-signature -v "$DMG_PATH"
  fi
fi

echo ""
echo "Build complete:"
echo "  App: $APP_BUNDLE ($(du -sh "$APP_BUNDLE" | cut -f1))"
if [[ "$SKIP_DMG" -eq 0 ]]; then
  echo "  DMG: $DMG_PATH ($(du -sh "$DMG_PATH" | cut -f1))"
fi
