const template = document.createElement("template");
template.innerHTML = `
    <style>
      :host { display: block; font-family: var(--paper-font-body1_); }
      ha-card { padding: 12px; }
      .header { display:flex; align-items:center; justify-content:space-between; gap:12px; }
      .title { font-weight: 500; font-size: 16px; }
      .content { display:flex; align-items:center; gap:8px; margin-top:12px; }

      .image { flex: 1 1 auto; display:flex; align-items:center; justify-content:center; }
      .feeder {
        width: 160px;
        height: 256px;
        border-radius: 8px;
        object-fit: cover;
      }

      .info-label {
        font-weight: 600;
        font-size: 18px;
        display: flex; align-items:center;
        justify-content:center;
        color: var(--primary-text-color);
        padding-bottom: 15px;
      }

      .error-label {
        height: 20px;
        text-align: center;
        font-size: 0.85em;
        font-weight: 500;
        line-height: 20px;
      }

      .controls { width: 160px; display:flex; flex-direction:column; gap:12px; align-items:stretch; }
      mwc-button { --mdc-theme-primary: var(--primary-color); width:100%; }
      .small { font-size: 12px; color: var(--secondary-text-color); }

      ha-button {
        width: 100%;
      }
      .snack {
        --mdc-theme-primary: var(--secondary-text-color);
      }

      .status-warning {
        color: #ff9800;
      }

      .status-error {
        color: #f44336;
      }
    </style>
    <ha-card>
      <div class="header">
        <div class="title" id="title">Alfeedo</div>
        <div class="small" id="last_updated"></div>
      </div>
      <div class="content">
        <div class="image">
          <img id="feeder_img" class="feeder" alt="Feeder image" src="">
        </div>

        <div class="controls">
          <div class="info-label" id="state_label">--</div>
          <div class="info-label" id="fill_label">--%</div>
          <div id="status_message" class="error-label"></div>
          <ha-button class="meal" unelevated>Feed Meal</ha-button>
          <ha-button class="snack" outlined>Feed Snack</ha-button>
        </div>
      </div>
    </ha-card>
  `;

class AlfeedoCard extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
    this._root.appendChild(template.content.cloneNode(true));
    this._hass = null;
    this._config = null;
    this._entitiesResolved = false;

    this._statusMsg = this._root.getElementById('status_message');
    this._fillLabel = this._root.getElementById('fill_label');
    this._stateLabel = this._root.getElementById("state_label");
    this._lastUpdated = this._root.getElementById("last_updated");
    this._img = this._root.getElementById("feeder_img");
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("Configuration for an alfeedo-card requires an entity");
    }
    this._config = config;

    this._root.getElementById("title").textContent = this._config.title || "Alfeedo";
    this._img = this._root.getElementById("feeder_img");
    if (this._img) {
      this._img.src = this._config.image || "/alfeedo/ui/img/feeder.png";
    }

    const btnMeal = this._root.querySelector(".meal");
    const btnSnack = this._root.querySelector(".snack");

    btnMeal.onclick = () => this._pressButton("meal");
    btnSnack.onclick = () => this._pressButton("snack");
  }

  static getConfigElement() {
    return document.createElement("alfeedo-card-editor");
  }

  static getStubConfig() {
    return { entity: "sensor.alfeedo_feeder_state", title: "Alfeedo" };
  }

  _pressButton(feedingType) {
    if (!this._hass || !this._config.entity) return;

    // Prefer optional explicit button entity configs. If not set, guess from main entity (state sensor)
    let buttonId;
    if (feedingType === 'meal' && this._config.meal_button) {
      buttonId = this._config.meal_button;
    } else if (feedingType === 'snack' && this._config.snack_button) {
      buttonId = this._config.snack_button;
    } else {
      buttonId = this._config.entity.replace('sensor.', 'button.').replace('_feeder_state', '_feed_' + feedingType);
    }

    this._hass.callService("button", "press", { entity_id: buttonId });
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;

    const entity = this._config.entity;
    if (!entity) {
      console.log("alfeedo-card: entity not configured.")
      return;
    }

    const stateObj = hass.states[entity];
    if (!stateObj) {
      this._lastUpdated.textContent = "";
      return;
    }


    const value = stateObj.state;
    if (this._stateLabel) this._stateLabel.textContent = value;

    const fill_level = stateObj.attributes.fill_level;
    const num = Number(fill_level);
    const pct = Number.isFinite(num) ? Math.max(0, Math.min(100, Math.round(num))) : null;
    const errorState = stateObj.attributes.error_state;
    if (pct !== null) {
      this._fillLabel.textContent = `${pct}%`;
      if (this._img) {
        let fixedValue = pct;
        if (Math.round(pct) > 0) {
          fixedValue = Math.max(1, Math.round(pct / 10) * 10);
        }
        const fillImg = "/alfeedo/ui/img/feeder transparent " + fixedValue + " " + errorState + ".png";
        console.log("alfeedo-card: setting image to", fillImg);
        this._img.src = fillImg;
      }
    } else {
      this._fillLabel.textContent = `${value}`;
      if (this._img) {
        const fillImg = "/alfeedo/ui/img/feeder.png";
        this._img.src = this._config.image || fillImg;
      }
    }

    switch (errorState) {
      case "ok":
        this._statusMsg.innerText = "";
        break;
      case "struggling":
        this._statusMsg.innerText = "The feeder is struggling"
        this._statusMsg.className = "error-label status-warning";
        break;
      case "jammed":
        this._statusMsg.innerText = "The feeder may be jammed"
        this._statusMsg.className = "error-label status-error";
        break;
    }

    this._lastUpdated.textContent = stateObj.last_updated ? new Date(stateObj.last_updated).toLocaleString() : "";

  }

  getCardSize() {
    return 3;
  }
}

class AlfeedoCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  // 1. HA calls this when the config changes
  setConfig(config) {
    this._config = config;
    this._render();
  }

  // 2. HA calls this to pass the hass object
  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;

    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => this._valueChanged(ev));
      this.shadowRoot.appendChild(this._form);

      this._form.computeLabel = (schema) => {
        return schema.label || schema.name;
      };
    }

    const schema = [
      { name: "title", selector: { text: {} } },
      {
        name: "entity",
        label: "Feeder Status Sensor",
        selector: { entity: { domain: "sensor", integration: "alfeedo" } }
      },
      {
        name: "meal_button",
        label: "Meal Button (Optional)",
        selector: { entity: { domain: "button", integration: "alfeedo" } }
      },
      {
        name: "snack_button",
        label: "Snack Button (Optional)",
        selector: { entity: { domain: "button", integration: "alfeedo" } }
      },
      { name: "image", label: "Custom Image URL", selector: { text: {} } }
    ];

    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = schema;
  }

  _valueChanged(ev) {
    // Standard event to save card settings
    const event = new CustomEvent("config-changed", {
      detail: { config: ev.detail.value },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

// Define only if not already registered (defensive)
if (!customElements.get("alfeedo-card")) {
  customElements.define("alfeedo-card", AlfeedoCard);
  console.debug("alfeedo-card: defined");
} else {
  console.debug("alfeedo-card: already defined");
}

customElements.define("alfeedo-card-editor", AlfeedoCardEditor);

// Make Lovelace aware of the custom card (helps the UI list it)
window.customCards = window.customCards || [];
window.customCards.push({
  type: "alfeedo-card",
  name: "Alfeedo Card",
  preview: true,
  description: "A custom card to monitor and trigger your Alfeedo cat feeder.",
});
