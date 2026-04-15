# Block Unit Testing (Optional)

Block unit tests are **optional** and should only be added when the block contains isolatable pure logic worth testing.

## When to Add Block Unit Tests

**Skip entirely** for:
- Decorative or presentational blocks (hero, teaser with only styling)
- Wiring-only code (event delegation, `decorate()` structure, param passing)
- Blocks with no calculations, validation, or state transitions
- Thin wrappers around third-party libraries

**Test when:** Logic is self-contained, has clear inputs/outputs, and assertions provide confidence without brittle setup.

**Good test candidates:** Extracted pure functions, calculations, business logic methods, state transitions, validation rules, timer/interval behavior, analytics payload building.

**Poor test candidates:** `decorate()` orchestration, DOM element caching, trivial selector lookups, simple property assignments.

## Testing Principle

**Default: Do NOT add unit tests** unless the spec explicitly requests them or the block has isolatable logic.

Focus on event handlers, state changes, calculations, and user-facing behavior. Do not test every function—test logic that delivers value.

## Assert All Outcomes of an Event Handler

When an event handler produces multiple changes, assert **all of them**.

```javascript
// ❌ Incomplete — CSS class checked, ARIA and button state ignored
button.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
expect(option.classList.contains('option--active')).toBe(true);

// ✅ Complete — all observable outcomes from the same handler
button.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
expect(option.classList.contains('option--active')).toBe(true);
expect(option.getAttribute('aria-checked')).toBe('true');
expect(confirmButton.disabled).toBe(false);
```

## Scope DOM Queries to Match Block Behavior

Query selectors in tests must mirror the scope the block uses at runtime.

```javascript
// ❌ Queries all options across all sections — wrong scope
const options = container.querySelectorAll('.block-name__option');
const lastOption = options[options.length - 1];

// ✅ Scope to the active section, matching how the handler works
const activeSection = container.querySelector('.block-name__section--active');
const activeOptions = activeSection.querySelectorAll('.block-name__option');
const lastOption = activeOptions[activeOptions.length - 1];
```

## Block HTML Fixtures

Use sample block DOM that matches the structure authors create. Fixtures live under `test/fixtures/blocks/` or `drafts/tmp/`.

```javascript
// test/blocks/countdown/countdown.test.js
import { describe, it, expect, beforeEach } from 'vitest';
import { readFileSync } from 'fs';
import { JSDOM } from 'jsdom';
import decorate from '../../../blocks/countdown/countdown.js';

function loadFixture(name) {
  const html = readFileSync(`test/fixtures/blocks/${name}.html`, 'utf-8');
  const dom = new JSDOM(html);
  return dom.window.document.body;
}

describe('countdown', () => {
  let block;

  beforeEach(async () => {
    const body = loadFixture('countdown-basic');
    block = body.querySelector('.countdown');
    await decorate(block);
  });

  it('should enable submit when input is valid', () => {
    // Test isolatable logic
  });
});
```

## Test Naming

Use descriptive `it()` descriptions that match **exactly** what is asserted. If the name implies multiple keys or directions, the test must cover them — or use a narrower name.

```javascript
// ❌ Name promises "arrow keys" (plural) but only tests one direction
it('should navigate between options with arrow keys', () => { ... });

// ✅ One test per case, names match exactly what is verified
it('should move selection to next option with ArrowRight', () => { });
it('should wrap to last option with ArrowLeft from first option', () => { });
```

Cover boundary/wrap-around cases when modulo or index arithmetic is involved — that is where bugs hide.

## Paths

- Block JS: `blocks/{block-name}/{block-name}.js`
- Block CSS: `blocks/{block-name}/{block-name}.css`
- Fixtures: `test/fixtures/blocks/{block-name}/` or `drafts/tmp/`
