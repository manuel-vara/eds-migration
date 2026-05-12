/**
 * Icon Grid Block
 * Grid of icon cards, each with an icon, title, and optional description.
 * @param {Element} block The icon-grid block element
 */
export default function decorate(block) {
  const ul = document.createElement('ul');

  [...block.children].forEach((row) => {
    const li = document.createElement('li');
    li.className = 'icon-grid-item';

    const cols = [...row.children];
    if (cols.length >= 2) {
      cols[0].className = 'icon-grid-icon';
      cols[1].className = 'icon-grid-content';
    } else if (cols.length === 1) {
      cols[0].className = 'icon-grid-content';
    }
    while (row.firstElementChild) li.append(row.firstElementChild);
    ul.append(li);
  });

  block.textContent = '';
  block.append(ul);
}
