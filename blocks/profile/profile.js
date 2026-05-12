/**
 * Profile Block
 * Expert profile with photo, name, title, credentials.
 * Row: col1 = photo, col2 = name + title + credentials
 * Variants: expert, bd-team
 * @param {Element} block The profile block element
 */
export default function decorate(block) {
  const rows = [...block.children];
  rows.forEach((row) => {
    const cols = [...row.children];
    if (cols.length >= 2) {
      cols[0].classList.add('profile-photo');
      cols[1].classList.add('profile-info');
    } else if (cols.length === 1) {
      const pic = cols[0].querySelector('picture');
      if (pic) {
        cols[0].classList.add('profile-photo');
      } else {
        cols[0].classList.add('profile-info');
      }
    }
  });
}
