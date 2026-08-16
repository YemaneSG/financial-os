import { writeFileSync } from 'node:fs';

const [mode, expectedText, outputPath] = process.argv.slice(2);

if (
  !['present', 'absent', 'arm-app-url-event', 'app-url-event-seen'].includes(mode) ||
  !expectedText ||
  !outputPath
) {
  console.error('A WebView assertion mode, expected text, and output path are required.');
  process.exit(2);
}

const delay = (milliseconds) =>
  new Promise((resolve) => setTimeout(resolve, milliseconds));

async function evaluateExpression(webSocketUrl, expression) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(webSocketUrl);
    const timeout = setTimeout(() => {
      socket.close();
      reject(new Error('DevTools evaluation timed out.'));
    }, 3_000);

    socket.addEventListener('open', () => {
      socket.send(
        JSON.stringify({
          id: 1,
          method: 'Runtime.evaluate',
          params: {
            expression,
            awaitPromise: true,
            returnByValue: true,
          },
        }),
      );
    });

    socket.addEventListener('message', (event) => {
      let response;
      try {
        response = JSON.parse(String(event.data));
      } catch {
        return;
      }

      if (response.id !== 1) {
        return;
      }

      clearTimeout(timeout);
      socket.close();
      if (response.error || response.result?.exceptionDetails) {
        reject(new Error('DevTools evaluation failed.'));
        return;
      }

      resolve(response.result?.result?.value);
    });

    socket.addEventListener('error', () => {
      clearTimeout(timeout);
      reject(new Error('DevTools socket failed.'));
    });
  });
}

async function readExpression(expression) {
  const response = await fetch('http://127.0.0.1:9222/json', {
    signal: AbortSignal.timeout(2_000),
  });
  if (!response.ok) {
    throw new Error('DevTools target lookup failed.');
  }

  const targets = await response.json();
  const target = targets.find(
    (candidate) =>
      candidate.type === 'page' && typeof candidate.webSocketDebuggerUrl === 'string',
  );
  if (!target) {
    throw new Error('No debuggable WebView target was found.');
  }

  return evaluateExpression(target.webSocketDebuggerUrl, expression);
}

const bodyTextExpression = 'document.body?.innerText ?? ""';
const appUrlEventFlag = '__financialOsPm0bSawAppUrlOpen';
const armAppUrlEventExpression = `
  (async () => {
    globalThis.${appUrlEventFlag} = false;
    globalThis.__financialOsPm0bAppUrlHandle = await globalThis.Capacitor.Plugins.App.addListener(
      'appUrlOpen',
      () => { globalThis.${appUrlEventFlag} = true; },
    );
    return true;
  })()
`;

if (mode === 'arm-app-url-event') {
  try {
    const armed = await readExpression(armAppUrlEventExpression);
    if (armed === true) {
      writeFileSync(outputPath, 'app-url-event-armed', { encoding: 'utf8', mode: 0o600 });
      process.exit(0);
    }
  } catch {
    // Fall through to the privacy-safe diagnostic below.
  }
  console.error('The direct App URL event observer could not be armed.');
  process.exit(1);
}

const timeoutMilliseconds =
  mode === 'absent' ? 5_000 : 30_000;
const deadline = Date.now() + timeoutMilliseconds;
let observedDom = false;
let lastFailure = 'The WebView debug endpoint was not reachable.';

while (Date.now() < deadline) {
  try {
    if (mode === 'app-url-event-seen') {
      const eventSeen = await readExpression(`Boolean(globalThis.${appUrlEventFlag})`);
      if (eventSeen === true) {
        writeFileSync(outputPath, 'app-url-event-seen', { encoding: 'utf8', mode: 0o600 });
        process.exit(0);
      }
      lastFailure = 'The native App URL event was not observed.';
      await delay(500);
      continue;
    }

    const bodyText = String(await readExpression(bodyTextExpression));
    observedDom = true;
    writeFileSync(outputPath, bodyText, { encoding: 'utf8', mode: 0o600 });

    const containsExpectedText = bodyText.includes(expectedText);
    if (mode === 'present' && containsExpectedText) {
      process.exit(0);
    }
    if (mode === 'absent' && containsExpectedText) {
      console.error('Unexpected WebView state was observed.');
      process.exit(1);
    }
    lastFailure = 'The WebView DOM was reachable but the expected text was absent.';
  } catch (error) {
    if (error instanceof Error) {
      lastFailure = error.message;
    }
    // The WebView target can briefly disappear during a cold start or resume.
  }

  await delay(500);
}

if (mode === 'absent' && observedDom) {
  process.exit(0);
}

console.error(`Expected privacy-safe WebView state was not observed. ${lastFailure}`);
process.exit(1);
