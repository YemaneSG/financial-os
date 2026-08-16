import { writeFileSync } from 'node:fs';

const [mode, expectedText, outputPath] = process.argv.slice(2);

if (!['present', 'absent'].includes(mode) || !expectedText || !outputPath) {
  console.error('A WebView assertion mode, expected text, and output path are required.');
  process.exit(2);
}

const delay = (milliseconds) =>
  new Promise((resolve) => setTimeout(resolve, milliseconds));

async function evaluateBodyText(webSocketUrl) {
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
            expression: 'document.body?.innerText ?? ""',
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

      resolve(String(response.result?.result?.value ?? ''));
    });

    socket.addEventListener('error', () => {
      clearTimeout(timeout);
      reject(new Error('DevTools socket failed.'));
    });
  });
}

async function readBodyText() {
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

  return evaluateBodyText(target.webSocketDebuggerUrl);
}

const timeoutMilliseconds = mode === 'present' ? 30_000 : 5_000;
const deadline = Date.now() + timeoutMilliseconds;
let observedDom = false;

while (Date.now() < deadline) {
  try {
    const bodyText = await readBodyText();
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
  } catch {
    // The WebView target can briefly disappear during a cold start or resume.
  }

  await delay(500);
}

if (mode === 'absent' && observedDom) {
  process.exit(0);
}

console.error('Expected privacy-safe WebView state was not observed.');
process.exit(1);
