import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

const [baselinePath, candidatePath, outputPath] = process.argv.slice(2);
const baseline = fs.readFileSync(baselinePath, 'utf8');
const candidate = fs.readFileSync(candidatePath, 'utf8');
const marker = '// Apply English display rules after data parsing, never to CSV/script delimiters.';
function load(text) {
  assert.equal(text.split(marker).length, 2, 'one original display helper');
  const capture = { exports: {} };
  const start = text.indexOf(marker), closing = '})(globalThis);';
  const end = text.indexOf(closing, start);
  assert.ok(end > start, 'bounded original display helper');
  new Function('module', text.slice(start, end + closing.length))(capture);
  assert.equal(typeof capture.exports.punctuation, 'function');
  return capture.exports;
}
const old = load(baseline), next = load(candidate);
let checks = 0, targetCases = 0, unchangedCases = 0;
const equal = (a, b, message) => { assert.equal(a, b, message); checks++; };

// The native formatter supplies ASCII commas without any space.
const native = '1,234.567MB/2,345.678MB';
equal(old.punctuation(native), '1，234.567MB/2，345.678MB', 'baseline creates fullwidth commas');
equal(old.punctuation(native).includes(' '), false, 'baseline gap is not an ASCII space');
equal(old.width(old.punctuation(native), 20) - old.width(native, 20), 20,
      'two fullwidth commas add two half-cell widths in the existing helper');
equal(next.punctuation(native), native, 'native ASCII separators survive');

const numbers = ['0', '0.001', '1.000', '123.456', '999.999', '1,000.000',
  '1,234.567', '12,345.678', '123,456.789', '1,234,567.890', '12,345,678.901'];
const commas = [',', '，'];
const spaces = ['', ' ', '\t', '\u00a0', '\u3000', ' \t\u00a0\u3000'];
for (const a of numbers) for (const b of numbers) for (const comma of commas) for (const space of spaces) {
  const original = `${a}MB/${b}MB`;
  const input = original.replaceAll(',', comma + space);
  equal(old.punctuation(input), original.replaceAll(',', '，'),
        'baseline already strips every supported horizontal space after a grouping comma');
  equal(next.punctuation(input), original, `compact counter ${JSON.stringify(input)}`);
  equal(next.format(input, 10000, 20, false), original, 'existing format uses the same helper');
  targetCases++;
}

// Prose, tags, numeric-only counts and unrelated size displays keep every old rule.
const unrelated = ['Hello, world', 'Hello， world', 'Hello,\tworld', 'Hello，\u3000world',
  '1,234/2,345', '1234/2345', '50%', '1,234.567MB', '1,234.567KB/2,345.678KB',
  '1,234.567GB/2,345.678GB', '1,234.567Mb/2,345.678Mb', '1,234.567MB /2,345.678MB',
  '1,234.567MB/ 2,345.678MB', 'Downloaded 1,234.567MB/2,345.678MB',
  '1,234.567MB/2,345.678MB downloaded', '<color=red>1,234.567MB/2,345.678MB</color>',
  '<tag name="a, b">Hello, world</tag>', '日本語， 文', '日本語, 文',
  '1,23.456MB/2,345.678MB', '1,234.56MB/2,345.678MB', '1,234.5678MB/2,345.678MB',
  '-1,234.567MB/2,345.678MB', '+1,234.567MB/2,345.678MB',
  '1,234.567MB/2,345.678MB\n', '1,234.567MB/2,345.678MB\r',
  '\n1,234.567MB/2,345.678MB', '1,\n234.567MB/2,345.678MB',
  '1,\r234.567MB/2,345.678MB', '1,\u2028234.567MB/2,345.678MB',
  '1,234.567MB/2,345.678MB\u2028', '1,234.567MB/2,345.678MB\u2029'];
for (const input of unrelated) {
  equal(next.punctuation(input), old.punctuation(input), `unrelated punctuation ${JSON.stringify(input)}`);
  for (const font of [7, 12, 20, 101]) for (const pixels of [0, 40, 180, 10000]) {
    equal(next.format(input, pixels, font, true), old.format(input, pixels, font, true),
          `unrelated wrap ${JSON.stringify(input)}`);
    equal(next.width(input, font), old.width(input, font), 'unchanged width helper');
  }
  unchangedCases++;
}
for (const comma of [',', '，']) for (const space of spaces) {
  const input = `A${comma}${space}B`;
  equal(next.punctuation(input), old.punctuation(input), 'all original English comma-spacing forms');
}
const digest = value => crypto.createHash('sha256').update(value).digest('hex');
const result = { schema: 'ffbe-download-spacing-formatter-tests-v1', passed: true,
  assertions: checks, native_counter_cases: targetCases, unrelated_cases: unchangedCases,
  baseline_script_sha256: digest(Buffer.from(baseline)), candidate_script_sha256: digest(Buffer.from(candidate)),
  baseline_wide_separator: 'U+FF0C', compact_separator: 'U+002C',
  baseline_has_u0020_gap: false, existing_helper_width_reduction_pixels_at_font20: 20,
  unchanged_generic_english_tags_wrapping_and_width: true, phone_rendering_tested: false };
if (outputPath) fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result));
