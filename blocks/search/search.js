import {
  createOptimizedPicture,
  decorateIcons,
} from '../../scripts/aem.js';

/**
 * Search Block
 * Site search using query-index.json.
 * Adapted from Block Collection.
 * @param {Element} block The search block element
 */

const searchParams = new URLSearchParams(window.location.search);

function findNextHeading(el) {
  let preceedingEl = el.parentElement.previousElementSibling || el.parentElement.parentElement;
  let h = 'H2';
  while (preceedingEl) {
    const lastHeading = [...preceedingEl.querySelectorAll('h1, h2, h3, h4, h5, h6')].pop();
    if (lastHeading) {
      const level = parseInt(lastHeading.nodeName[1], 10);
      h = level < 6 ? `H${level + 1}` : 'H6';
      preceedingEl = false;
    } else {
      preceedingEl = preceedingEl.previousElementSibling || preceedingEl.parentElement;
    }
  }
  return h;
}

function highlightTextElements(terms, elements) {
  elements.forEach((element) => {
    if (!element || !element.textContent) return;
    const matches = [];
    const { textContent } = element;
    terms.forEach((term) => {
      let start = 0;
      let offset = textContent.toLowerCase().indexOf(term.toLowerCase(), start);
      while (offset >= 0) {
        matches.push({ offset, term: textContent.substring(offset, offset + term.length) });
        start = offset + term.length;
        offset = textContent.toLowerCase().indexOf(term.toLowerCase(), start);
      }
    });
    if (!matches.length) return;
    matches.sort((a, b) => a.offset - b.offset);
    let currentIndex = 0;
    const fragment = matches.reduce((acc, { offset, term }) => {
      if (offset < currentIndex) return acc;
      const textBefore = textContent.substring(currentIndex, offset);
      if (textBefore) acc.appendChild(document.createTextNode(textBefore));
      const markedTerm = document.createElement('mark');
      markedTerm.textContent = term;
      acc.appendChild(markedTerm);
      currentIndex = offset + term.length;
      return acc;
    }, document.createDocumentFragment());
    const textAfter = textContent.substring(currentIndex);
    if (textAfter) fragment.appendChild(document.createTextNode(textAfter));
    element.innerHTML = '';
    element.appendChild(fragment);
  });
}

async function fetchData(source) {
  const response = await fetch(source);
  if (!response.ok) return null;
  const json = await response.json();
  if (!json) return null;
  return json.data;
}

function renderResult(result, searchTerms, titleTag) {
  const li = document.createElement('li');
  const a = document.createElement('a');
  a.href = result.path;
  if (result.image) {
    const wrapper = document.createElement('div');
    wrapper.className = 'search-result-image';
    const pic = createOptimizedPicture(result.image, '', false, [{ width: '375' }]);
    wrapper.append(pic);
    a.append(wrapper);
  }
  if (result.title) {
    const title = document.createElement(titleTag);
    title.className = 'search-result-title';
    const link = document.createElement('a');
    link.href = result.path;
    link.textContent = result.title;
    highlightTextElements(searchTerms, [link]);
    title.append(link);
    a.append(title);
  }
  if (result.description) {
    const description = document.createElement('p');
    description.textContent = result.description;
    highlightTextElements(searchTerms, [description]);
    a.append(description);
  }
  li.append(a);
  return li;
}

function clearSearchResults(block) {
  block.querySelector('.search-results').innerHTML = '';
}

function clearSearch(block) {
  clearSearchResults(block);
  if (window.history.replaceState) {
    const url = new URL(window.location.href);
    url.search = '';
    searchParams.delete('q');
    window.history.replaceState({}, '', url.toString());
  }
}

function filterData(searchTerms, data) {
  const foundInHeader = [];
  const foundInMeta = [];
  data.forEach((result) => {
    let minIdx = -1;
    searchTerms.forEach((term) => {
      const idx = (result.header || result.title || '').toLowerCase().indexOf(term);
      if (idx >= 0 && (minIdx < 0 || idx < minIdx)) minIdx = idx;
    });
    if (minIdx >= 0) {
      foundInHeader.push({ minIdx, result });
      return;
    }
    const metaContents = `${result.title || ''} ${result.description || ''} ${(result.path || '').split('/').pop()}`.toLowerCase();
    searchTerms.forEach((term) => {
      const idx = metaContents.indexOf(term);
      if (idx >= 0 && (minIdx < 0 || idx < minIdx)) minIdx = idx;
    });
    if (minIdx >= 0) foundInMeta.push({ minIdx, result });
  });
  const compare = (a, b) => a.minIdx - b.minIdx;
  return [...foundInHeader.sort(compare), ...foundInMeta.sort(compare)].map((item) => item.result);
}

async function handleSearch(e, block, config) {
  const searchValue = e.target.value;
  searchParams.set('q', searchValue);
  if (window.history.replaceState) {
    const url = new URL(window.location.href);
    url.search = searchParams.toString();
    window.history.replaceState({}, '', url.toString());
  }
  if (searchValue.length < 3) {
    clearSearch(block);
    return;
  }
  const searchTerms = searchValue.toLowerCase().split(/\s+/).filter((term) => !!term);
  const data = await fetchData(config.source);
  const filteredData = filterData(searchTerms, data);

  const searchResults = block.querySelector('.search-results');
  searchResults.innerHTML = '';
  const headingTag = searchResults.dataset.h;

  if (filteredData.length) {
    searchResults.classList.remove('no-results');
    filteredData.forEach((result) => {
      searchResults.append(renderResult(result, searchTerms, headingTag));
    });
  } else {
    searchResults.classList.add('no-results');
    const noResults = document.createElement('li');
    noResults.textContent = 'No results found.';
    searchResults.append(noResults);
  }
}

export default async function decorate(block) {
  const source = block.querySelector('a[href]') ? block.querySelector('a[href]').href : '/query-index.json';
  block.innerHTML = '';

  const box = document.createElement('div');
  box.classList.add('search-box');

  const icon = document.createElement('span');
  icon.classList.add('icon', 'icon-search');
  box.append(icon);

  const input = document.createElement('input');
  input.setAttribute('type', 'search');
  input.className = 'search-input';
  input.placeholder = 'Search...';
  input.setAttribute('aria-label', 'Search');
  input.addEventListener('input', (e) => handleSearch(e, block, { source }));
  input.addEventListener('keyup', (e) => { if (e.code === 'Escape') clearSearch(block); });
  box.append(input);

  const results = document.createElement('ul');
  results.className = 'search-results';
  results.dataset.h = findNextHeading(block);
  results.setAttribute('role', 'status');
  results.setAttribute('aria-live', 'polite');
  results.setAttribute('aria-atomic', true);

  block.append(box, results);

  if (searchParams.get('q')) {
    input.value = searchParams.get('q');
    input.dispatchEvent(new Event('input'));
  }

  decorateIcons(block);
}
