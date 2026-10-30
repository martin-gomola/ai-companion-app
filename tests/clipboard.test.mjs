import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../src/yourturn/static/app.js', import.meta.url), 'utf8');
const handler = source.slice(source.indexOf('async function copyThreadId()'), source.indexOf('$("copy-thread-id").addEventListener'));

for (const denied of [false, true]) {
  test(`copy Thread ID: ${denied ? 'denied' : 'success'}`, async () => {
    const id = '0d3e0067-0000-7000-8000-000000000067';
    const nodes = { 'session-thread-id': { textContent: id }, 'copy-thread-id': { disabled: false }, 'copy-thread-status': { textContent: '' } };
    let copied;
    const context = vm.createContext({ $: key => nodes[key], navigator: { clipboard: { writeText: async value => {
      if (denied) throw new Error('Clipboard denied');
      copied = value;
    } } } });
    vm.runInContext(handler, context);
    await context.copyThreadId();
    assert.equal(nodes['session-thread-id'].textContent, id);
    assert.match(nodes['copy-thread-status'].textContent, denied ? /copy it manually/ : /copied/);
    assert.equal(copied, denied ? undefined : id);
  });
}
