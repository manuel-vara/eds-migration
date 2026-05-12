import { readBlockConfig } from '../../scripts/aem.js';

/**
 * HubSpot Form Block
 * Loads a HubSpot form by portal and form ID.
 * Configuration table: Row1: Portal ID | value, Row2: Form ID | value
 * @param {Element} block The hubspot-form block element
 */

let hsScriptLoaded = false;

function loadHubSpotScript() {
  if (hsScriptLoaded) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://js.hsforms.net/forms/v2.js';
    script.async = true;
    script.onload = () => {
      hsScriptLoaded = true;
      resolve();
    };
    script.onerror = reject;
    document.head.append(script);
  });
}

export default async function decorate(block) {
  const config = readBlockConfig(block);
  const portalId = config['portal-id'] || config.portalid || '';
  const formId = config['form-id'] || config.formid || '';

  block.textContent = '';

  if (!portalId || !formId) {
    block.innerHTML = '<p>HubSpot form configuration missing.</p>';
    return;
  }

  const formContainer = document.createElement('div');
  formContainer.className = 'hubspot-form-container';
  formContainer.id = `hs-form-${formId}`;
  block.append(formContainer);

  const observer = new IntersectionObserver(async (entries) => {
    if (entries.some((e) => e.isIntersecting)) {
      observer.disconnect();
      try {
        await loadHubSpotScript();
        if (window.hbspt) {
          window.hbspt.forms.create({
            portalId,
            formId,
            target: `#${formContainer.id}`,
          });
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Failed to load HubSpot form', error);
      }
    }
  });
  observer.observe(block);
}
