/**
 * Breadcrumbs Block
 * Auto-generated breadcrumb navigation from URL path.
 * @param {Element} block The breadcrumbs block element
 */
function toTitle(slug) {
  return slug
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default function decorate(block) {
  const { pathname } = window.location;
  const segments = pathname.split('/').filter(Boolean);

  const nav = document.createElement('nav');
  nav.setAttribute('aria-label', 'Breadcrumb');

  const ol = document.createElement('ol');

  // home link
  const homeLi = document.createElement('li');
  const homeLink = document.createElement('a');
  homeLink.href = '/';
  homeLink.textContent = 'Home';
  homeLi.append(homeLink);
  ol.append(homeLi);

  let path = '';
  segments.forEach((segment, idx) => {
    path += `/${segment}`;
    const li = document.createElement('li');
    if (idx === segments.length - 1) {
      li.setAttribute('aria-current', 'page');
      li.textContent = toTitle(segment);
    } else {
      const a = document.createElement('a');
      a.href = path;
      a.textContent = toTitle(segment);
      li.append(a);
    }
    ol.append(li);
  });

  nav.append(ol);
  block.textContent = '';
  block.append(nav);
}
