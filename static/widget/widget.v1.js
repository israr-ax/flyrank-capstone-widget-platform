(function () {
  const script = document.currentScript;
  const widgetId = script.getAttribute('data-widget-id');
  const apiBase = script.getAttribute('data-api-base') || 'http://localhost:8000';

  if (!widgetId) {
    console.error('flyrank widget: missing data-widget-id attribute on script tag');
    return;
  }

  const host = document.createElement('div');
  script.parentNode.insertBefore(host, script.nextSibling);
  const shadow = host.attachShadow({ mode: 'open' });

  // Style is scoped INSIDE the shadow root — the customer's page CSS
  // can never leak in, and our styles can never leak out onto their page.
  const style = document.createElement('style');
  style.textContent = `
    .fr-widget { font-family: system-ui, sans-serif; max-width: 360px; padding: 16px;
                 border: 1px solid #ddd; border-radius: 8px; }
    .fr-title { font-weight: 600; margin-bottom: 4px; }
    .fr-desc { font-size: 14px; color: #555; margin-bottom: 12px; }
    .fr-field { margin-bottom: 10px; }
    .fr-field label { display: block; font-size: 13px; margin-bottom: 4px; }
    .fr-field input { width: 100%; padding: 8px; box-sizing: border-box;
                       border: 1px solid #ccc; border-radius: 4px; }
    .fr-button { background: #111; color: #fff; border: none; padding: 10px 16px;
                 border-radius: 4px; cursor: pointer; width: 100%; }
    .fr-status { font-size: 13px; margin-top: 8px; }
    .fr-hp { position: absolute; left: -9999px; }
  `;
  shadow.appendChild(style);

  const container = document.createElement('div');
  container.className = 'fr-widget';
  shadow.appendChild(container);
  container.textContent = 'Loading...';

  fetch(`${apiBase}/api/widgets/${widgetId}/config/`)
    .then((res) => {
      if (!res.ok) throw new Error('widget not found');
      return res.json();
    })
    .then((config) => renderForm(config))
    .catch(() => {
      container.textContent = '';
    });

  function renderForm(config) {
    container.innerHTML = '';

    const title = document.createElement('div');
    title.className = 'fr-title';
    title.textContent = config.title;
    container.appendChild(title);

    if (config.description) {
      const desc = document.createElement('div');
      desc.className = 'fr-desc';
      desc.textContent = config.description;
      container.appendChild(desc);
    }

    const form = document.createElement('form');
    const inputs = {};

    config.form_fields.forEach((field) => {
      const wrapper = document.createElement('div');
      wrapper.className = 'fr-field';

      const label = document.createElement('label');
      label.textContent = field.name + (field.required ? ' *' : '');
      wrapper.appendChild(label);

      const input = document.createElement('input');
      input.type = field.type === 'email' ? 'email' : 'text';
      input.name = field.name;
      if (field.required) input.required = true;
      wrapper.appendChild(input);

      inputs[field.name] = input;
      form.appendChild(wrapper);
    });

    // Honeypot — invisible to real visitors, catnip for bots that fill every field.
    const hp = document.createElement('input');
    hp.type = 'text';
    hp.name = 'hp_field';
    hp.className = 'fr-hp';
    hp.tabIndex = -1;
    hp.autocomplete = 'off';
    form.appendChild(hp);

    const button = document.createElement('button');
    button.type = 'submit';
    button.className = 'fr-button';
    button.textContent = config.button_text || 'Submit';
    form.appendChild(button);

    const status = document.createElement('div');
    status.className = 'fr-status';

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const data = {};
      Object.keys(inputs).forEach((name) => { data[name] = inputs[name].value; });

      button.disabled = true;
      status.textContent = 'Sending...';

      fetch(`${apiBase}/api/submissions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ widget_id: widgetId, data, hp_field: hp.value }),
      })
        .then((res) => {
          if (!res.ok) throw new Error('submission failed');
          return res.json();
        })
        .then(() => {
          status.textContent = 'Thanks! Received.';
          form.reset();
        })
        .catch(() => {
          status.textContent = 'Something went wrong — please try again.';
        })
        .finally(() => { button.disabled = false; });
    });

    container.appendChild(form);
    container.appendChild(status);
  }
})();