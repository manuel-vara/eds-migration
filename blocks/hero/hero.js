/**
 * Hero Block
 * Full-width banner with background image, heading, subtitle, and CTA.
 * @param {Element} block The hero block element
 */
export default function decorate(block) {
  const rows = [...block.children];
  rows.forEach((row) => {
    const cols = [...row.children];
    if (cols.length >= 2) {
      cols[0].classList.add('hero-image');
      cols[1].classList.add('hero-content');
    } else if (cols.length === 1) {
      const pic = cols[0].querySelector('picture');
      if (pic) {
        cols[0].classList.add('hero-image');
      } else {
        cols[0].classList.add('hero-content');
      }
    }
  });
}
