#!/usr/bin/env bash

set -euo pipefail

readonly APP_ID="dev.financialos.premium.proof"
readonly MAIN_ACTIVITY="${APP_ID}/.MainActivity"
readonly COMPLETION_URI="${APP_ID}://plaid/complete"
readonly EXPECTED_TITLE="PM-0B native return proof"
readonly EXPECTED_RETURN_STATUS="Return received. Checking the bound server session"

apk_path="${1:-}"
evidence_dir="${RUNNER_TEMP:-/tmp}/financial-os-pm0b-android"
ui_dump_device="/data/local/tmp/financial-os-pm0b-ui.xml"
ui_dump_local="${evidence_dir}/ui.xml"
logcat_local="${evidence_dir}/logcat.txt"
storage_local="${evidence_dir}/app-storage.tar"

if [[ -z "${apk_path}" || ! -f "${apk_path}" ]]; then
  echo "Usage: $0 /absolute/path/to/app-debug.apk" >&2
  exit 2
fi

mkdir -p "${evidence_dir}"

cleanup() {
  adb emu kill >/dev/null 2>&1 || true
}

trap cleanup EXIT

wait_for_text() {
  local expected="$1"

  for _ in {1..30}; do
    adb shell uiautomator dump "${ui_dump_device}" >/dev/null 2>&1 || true
    adb pull "${ui_dump_device}" "${ui_dump_local}" >/dev/null 2>&1 || true
    if [[ -f "${ui_dump_local}" ]] && grep -Fq "${expected}" "${ui_dump_local}"; then
      return 0
    fi
    sleep 1
  done

  echo "Expected privacy-safe UI state was not observed." >&2
  exit 1
}

assert_text_absent() {
  local unexpected="$1"

  adb shell uiautomator dump "${ui_dump_device}" >/dev/null 2>&1
  adb pull "${ui_dump_device}" "${ui_dump_local}" >/dev/null 2>&1
  if grep -Fq "${unexpected}" "${ui_dump_local}"; then
    echo "Unexpected UI state was observed." >&2
    exit 1
  fi
}

clear_and_launch() {
  adb shell am force-stop "${APP_ID}" >/dev/null
  adb shell pm clear "${APP_ID}" >/dev/null
  adb shell am start -W -n "${MAIN_ACTIVITY}" >/dev/null
  wait_for_text "${EXPECTED_TITLE}"
  assert_text_absent "${EXPECTED_RETURN_STATUS}"
}

send_completion_return() {
  adb shell am start -W \
    -a android.intent.action.VIEW \
    -c android.intent.category.BROWSABLE \
    -d "${COMPLETION_URI}" >/dev/null
}

adb shell input keyevent KEYCODE_WAKEUP >/dev/null
adb shell wm dismiss-keyguard >/dev/null 2>&1 || true
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
adb logcat -c
adb install -r "${apk_path}" >/dev/null

# Interruption/cancel: no callback means no result is inferred.
clear_and_launch
adb shell input keyevent KEYCODE_HOME >/dev/null
adb shell am start -W -n "${MAIN_ACTIVITY}" >/dev/null
wait_for_text "${EXPECTED_TITLE}"
assert_text_absent "${EXPECTED_RETURN_STATUS}"

# Resume: an exact callback wakes the already-running app into a neutral state.
send_completion_return
wait_for_text "${EXPECTED_RETURN_STATUS}"

# Replay: repeating the same public, token-free callback remains only a wake-up.
send_completion_return
wait_for_text "${EXPECTED_RETURN_STATUS}"

# Cold start: the listener is installed before the launch URL is reduced.
adb shell am force-stop "${APP_ID}" >/dev/null
send_completion_return
wait_for_text "${EXPECTED_RETURN_STATUS}"

# Forgery: query material is rejected and never rendered.
clear_and_launch
adb shell am start -W \
  -a android.intent.action.VIEW \
  -c android.intent.category.BROWSABLE \
  -d "${COMPLETION_URI}?unexpected=synthetic" >/dev/null
wait_for_text "${EXPECTED_TITLE}"
assert_text_absent "${EXPECTED_RETURN_STATUS}"

# Keep raw diagnostic material private to the ephemeral runner and check only
# for prohibited credential-shaped data. Nothing is uploaded as an artifact.
adb logcat -d >"${logcat_local}"
adb exec-out run-as "${APP_ID}" sh -c \
  'tar -cf - shared_prefs cache app_webview 2>/dev/null || true' \
  >"${storage_local}"

if grep -aEiq \
  '(public_token|link_token|access_token|client_secret|authorization:[[:space:]]*bearer)' \
  "${ui_dump_local}" "${logcat_local}" "${storage_local}"; then
  echo "Credential-shaped callback material reached emulator evidence." >&2
  exit 1
fi

if ! adb shell pidof "${APP_ID}" >/dev/null; then
  echo "Application process was not healthy after the return matrix." >&2
  exit 1
fi

echo "Android emulator synthetic return matrix passed."
