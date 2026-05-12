import { readBlockConfig } from '../../scripts/aem.js';

/**
 * Content Filter Block
 * Filterable content listing with faceted filters, pagination.
 * Reads from query-index.json. Supports events, news, knowledge variants.
 * @param {Element} block The content-filter block element
 */

const PAGE_SIZE = 12;

async function fetchIndex(source) {
  const indexUrl = source.startsWith('http') ? source : '/query-index.json';
  const resp = await fetch(indexUrl);
  if (!resp.ok) return [];
  const json = await resp.json();
  return json.data || [];
}

function getFilterValues(data, field) {
  const values = new Set();
  data.forEach((item) => {
    const val = item[field];
    if (val) {
      val.split(',').forEach((v) => values.add(v.trim()));
    }
  });
  return [...values].sort();
}

function createFilterDropdown(label, field, values, onChange) {
  const wrapper = document.createElement('div');
  wrapper.className = 'filter-dropdown';

  const select = document.createElement('select');
  select.setAttribute('aria-label', `Filter by ${label}`);
  const defaultOpt = document.createElement('option');
  defaultOpt.value = '';
  defaultOpt.textContent = `All ${label}`;
  select.append(defaultOpt);

  values.forEach((val) => {
    const opt = document.createElement('option');
    opt.value = val;
    opt.textContent = val;
    select.append(opt);
  });

  select.addEventListener('change', () => onChange(field, select.value));
  wrapper.append(select);
  return wrapper;
}

function renderCard(item) {
  const card = document.createElement('div');
  card.className = 'filter-card';
  const link = document.createElement('a');
  link.href = item.path;

  if (item.image) {
    const imgWrapper = document.createElement('div');
    imgWrapper.className = 'filter-card-image';
    const img = document.createElement('img');
    img.src = item.image;
    img.alt = item.title || '';
    img.loading = 'lazy';
    imgWrapper.append(img);
    link.append(imgWrapper);
  }

  const body = document.createElement('div');
  body.className = 'filter-card-body';

  if (item.eventDate || item.publishDate) {
    const datep = document.createElement('p');
    datep.className = 'filter-card-date';
    const rawDate = item.eventDate || item.publishDate;
    const ts = Number(rawDate);
    datep.textContent = !Number.isNaN(ts) && ts > 0
      ? new Date(ts * 1000).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
      : rawDate;
    body.append(datep);
  }

  const title = document.createElement('h3');
  title.textContent = item.title || '';
  body.append(title);

  if (item.description) {
    const desc = document.createElement('p');
    desc.className = 'filter-card-desc';
    desc.textContent = item.description.length > 120
      ? `${item.description.substring(0, 120)}…`
      : item.description;
    body.append(desc);
  }

  if (item.eventLocation) {
    const loc = document.createElement('p');
    loc.className = 'filter-card-location';
    loc.textContent = item.eventLocation;
    body.append(loc);
  }

  link.append(body);
  card.append(link);
  return card;
}

function renderPagination(totalItems, currentPage, onPageChange) {
  const totalPages = Math.ceil(totalItems / PAGE_SIZE);
  if (totalPages <= 1) return null;

  const nav = document.createElement('nav');
  nav.className = 'filter-pagination';
  nav.setAttribute('aria-label', 'Pagination');

  if (currentPage > 1) {
    const prev = document.createElement('button');
    prev.type = 'button';
    prev.textContent = '← Previous';
    prev.addEventListener('click', () => onPageChange(currentPage - 1));
    nav.append(prev);
  }

  const info = document.createElement('span');
  info.className = 'filter-pagination-info';
  info.textContent = `Page ${currentPage} of ${totalPages}`;
  nav.append(info);

  if (currentPage < totalPages) {
    const next = document.createElement('button');
    next.type = 'button';
    next.textContent = 'Next →';
    next.addEventListener('click', () => onPageChange(currentPage + 1));
    nav.append(next);
  }

  return nav;
}

export default async function decorate(block) {
  const config = readBlockConfig(block);
  const source = config.source || '';
  block.textContent = '';

  // Build container
  const filtersContainer = document.createElement('div');
  filtersContainer.className = 'filter-controls';

  const resultsContainer = document.createElement('div');
  resultsContainer.className = 'filter-results';

  const paginationContainer = document.createElement('div');
  paginationContainer.className = 'filter-pagination-wrapper';

  const countContainer = document.createElement('div');
  countContainer.className = 'filter-count';

  block.append(filtersContainer, countContainer, resultsContainer, paginationContainer);

  // Fetch data
  const allData = await fetchIndex(source);

  // Filter by source path pattern
  let data = allData;
  if (source && !source.startsWith('http')) {
    data = allData.filter((item) => item.path && item.path.includes(`/${source}`));
  }

  const activeFilters = {};
  let currentPage = 1;

  function applyFilters() {
    let filtered = [...data];
    Object.entries(activeFilters).forEach(([field, value]) => {
      if (value) {
        filtered = filtered.filter((item) => {
          const itemVal = item[field] || '';
          return itemVal.toLowerCase().includes(value.toLowerCase());
        });
      }
    });
    return filtered;
  }

  function render() {
    const filtered = applyFilters();
    const start = (currentPage - 1) * PAGE_SIZE;
    const page = filtered.slice(start, start + PAGE_SIZE);

    resultsContainer.innerHTML = '';
    if (page.length === 0) {
      resultsContainer.innerHTML = '<p class="filter-no-results">No results found. Try adjusting your filters.</p>';
    } else {
      page.forEach((item) => resultsContainer.append(renderCard(item)));
    }

    countContainer.textContent = `${filtered.length} result${filtered.length !== 1 ? 's' : ''}`;

    paginationContainer.innerHTML = '';
    const pag = renderPagination(filtered.length, currentPage, (pg) => {
      currentPage = pg;
      render();
      block.scrollIntoView({ behavior: 'smooth' });
    });
    if (pag) paginationContainer.append(pag);
  }

  function onFilterChange(field, value) {
    activeFilters[field] = value;
    currentPage = 1;
    render();

    // Update URL params
    const url = new URL(window.location);
    if (value) {
      url.searchParams.set(field, value);
    } else {
      url.searchParams.delete(field);
    }
    window.history.replaceState({}, '', url);
  }

  // Build filter dropdowns from config
  const filterFields = Object.entries(config).filter(([key]) => key !== 'source');
  filterFields.forEach(([field]) => {
    const values = getFilterValues(data, field);
    if (values.length > 0) {
      const dd = createFilterDropdown(field, field, values, onFilterChange);
      filtersContainer.append(dd);
    }
  });

  // Restore filters from URL
  const urlParams = new URLSearchParams(window.location.search);
  filterFields.forEach(([field]) => {
    const urlVal = urlParams.get(field);
    if (urlVal) {
      activeFilters[field] = urlVal;
      const select = filtersContainer.querySelector(`select[aria-label="Filter by ${field}"]`);
      if (select) select.value = urlVal;
    }
  });

  render();
}
