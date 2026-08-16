#!/usr/bin/env bash

set -euo pipefail

readonly APP_ID="dev.financialos.premium.proof"
readonly MAIN_ACTIVITY="${APP_ID}/.MainActivity"
readonly COMPLETION_URI="${APP_ID}://plaid/complete"
readonly EXPECTED_TITLE="PM-0B native return proof"
readonly EXPECTED_RETURN_STATUS="Return received. Checking the bound server session"

apk_path="${1:-}"
evidence_dir="${RUNNER_TEMP:-/tmp}/financial-os-pm0b-android"
ui_state_local="${evidence_dir}/webview-state.txt"
logcat_local="${evidence_dir}/logcat.txt"
storage_local="${evidence_dir}/app-storage.tar"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${apk_path}" || ! -f "${apk_path}" ]]; then
  echo "Usage: $0 /absolute/path/to/app-debug.apk" >&2
  exit 2
fi

mkdir -p "${evidence_dir}"

cleanup() {
  adb emu kill >/dev/null 2>&1 || true
}

trap cleanup EXIT

forward_webview_debug() {
  for _ in {1..30}; do
    local app_pid
    app_pid="$(adb shell pidof "${APP_ID}" 2>/dev/null | tr -d '\r')"
    app_pid="${app_pid%% *}"
    if [[ -n "${app_pid}" ]]; then
      adb forward --remove tcp:9222 >/dev/null 2>&1 || true
      if adb forward \
        tcp:9222 \
        "localabstract:webview_devtools_remote_${app_pid}" >/dev/null; then
        return
      fi
    fi
    sleep 1
  done

  echo "A debuggable app process was not available." >&2
  exit 1
}

wait_for_text() {
  local expected="$1"
  local stage="$2"

  forward_webview_debug
  if ! node "${script_dir}/check-premium-mobile-webview-state.mjs" \
    present "${expected}" "${ui_state_local}"; then
    echo "WebView assertion failed during ${stage}." >&2
    exit 1
  fi
}

assert_text_absent() {
  local unexpected="$1"
  local stage="$2"

  forward_webview_debug
  if ! node "${script_dir}/check-premium-mobile-webview-state.mjs" \
    absent "${unexpected}" "${ui_state_local}"; then
    echo "WebView absence assertion failed during ${stage}." >&2
    exit 1
  fi
}

clear_and_launch() {
  adb shell am force-stop "${APP_ID}" >/dev/null
  adb shell pm clear "${APP_ID}" >/dev/null
  adb shell am start -W -n "${MAIN_ACTIVITY}" >/dev/null
  wait_for_text "${EXPECTED_TITLE}" "baseline launch"
  assert_text_absent "${EXPECTED_RETURN_STATUS}" "baseline launch"
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
wait_for_text "${EXPECTED_TITLE}" "interruption resume"
assert_text_absent "${EXPECTED_RETURN_STATUS}" "interruption resume"

# Resume: an exact callback wakes the already-running app into a neutral state.
send_completion_return
wait_for_text "${EXPECTED_RETURN_STATUS}" "warm callback resume"

# Replay: repeating the same public, token-free callback remains only a wake-up.
send_completion_return
wait_for_text "${EXPECTED_RETURN_STATUS}" "callback replay"

# Cold start: the listener is installed before the launch URL is reduced.
adb shell am force-stop "${APP_ID}" >/dev/null
send_completion_return
wait_for_text "${EXPECTED_RETURN_STATUS}" "cold-start callback"

# Forgery: query material is rejected and never rendered.
clear_and_launch
adb shell am start -W \
  -a android.intent.action.VIEW \
  -c android.intent.category.BROWSABLE \
  -d "${COMPLETION_URI}?unexpected=synthetic" >/dev/null
wait_for_text "${EXPECTED_TITLE}" "forged callback"
assert_text_absent "${EXPECTED_RETURN_STATUS}" "forged callback"

# Keep raw diagnostic material private to the ephemeral runner and check only
# for prohibited credential-shaped data. Nothing is uploaded as an artifact.
adb logcat -d >"${logcat_local}"
adb exec-out run-as "${APP_ID}" sh -c \
  'tar -cf - shared_prefs cache app_webview 2>/dev/null || true' \
  >"${storage_local}"

if grep -aEiq \
  '(public_token|link_token|access_token|client_secret|authorization:[[:space:]]*bearer)' \
  "${ui_state_local}" "${logcat_local}" "${storage_local}"; then
  echo "Credential-shaped callback material reached emulator evidence." >&2
  exit 1
fi

if ! adb shell pidof "${APP_ID}" >/dev/null; then
  echo "Application process was not healthy after the return matrix." >&2
  exit 1
fi

echo "Android emulator synthetic return matrix passed."
