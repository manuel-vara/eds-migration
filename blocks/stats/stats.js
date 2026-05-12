/**
 * Stats Block
 * Animated number counter display.
 * Each row: col1 = number value, col2 = label text
 * @param {Element} block The stats block element
 */
function animateCounter(el, target) {
  const duration = 2000;
  const startTime = performance.now();
  const isFloat = target % 1 !== 0;
  const suffix = el.dataset.suffix || '';

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - (1 - progress) ** 3;
    const current = eased * target;
    el.textContent = isFloat ? current.toFixed(1) + suffix : Math.floor(current) + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

export default function decorate(block) {
  const items = document.createElement('div');
  items.className = 'stats-grid';

  [...block.children].forEach((row) => {
    const cols = [...row.children];
    const item = document.createElement('div');
    item.className = 'stats-item';

    const numberEl = document.createElement('div');
    numberEl.className = 'stats-number';
    const raw = cols[0]?.textContent?.trim() || '0';
    const suffix = raw.replace(/[\d.,]/g, '');
    const numValue = parseFloat(raw.replace(/[^\d.]/g, ''));
    numberEl.textContent = '0';
    numberEl.dataset.target = numValue;
    numberEl.dataset.suffix = suffix;

    const label = document.createElement('div');
    label.className = 'stats-label';
    label.textContent = cols[1]?.textContent?.trim() || '';

    item.append(numberEl, label);
    items.append(item);
  });

  block.textContent = '';
  block.append(items);

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        observer.disconnect();
        block.querySelectorAll('.stats-number').forEach((el) => {
          animateCounter(el, parseFloat(el.dataset.target));
        });
      }
    });
  }, { threshold: 0.3 });
  observer.observe(block);
}
