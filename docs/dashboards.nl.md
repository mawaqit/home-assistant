# Dashboards voor MAWAQIT

[English](dashboards.md) | [Français](dashboards.fr.md) | [Deutsch](dashboards.de.md) | **Nederlands**

Drie voorbeelden om in je dashboards te plakken:

- [Gebedstijdenkaart](#gebedstijdenkaart): de foto van je moskee, de Hijri-datum van vandaag, het volgende gebed en de adhan en iqama van elk gebed. Alleen ingebouwde kaarten.
- [Volgend gebed](#volgend-gebed): een kleine kaart met het volgende gebed en de resterende tijd. Alleen ingebouwde kaarten.
- [Moskeescherm](#moskeescherm): een schermvullende weergave zoals de schermen van je moskee, voor een tablet aan de muur. Hiervoor is [button-card](https://github.com/custom-cards/button-card) nodig, geïnstalleerd met HACS.

Een kaart toevoegen: open je dashboard, kies ✏️ **Dashboard bewerken** en daarna **Kaart toevoegen**. Zoek naar **Handmatig**, plak de YAML en kies **Opslaan**.

## Gebedstijdenkaart

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="images/dashboards/prayer-times-card-dark.jpg">
  <img alt="Gebedstijdenkaart met de foto van de moskee, de Hijri-datum, het volgende gebed en de tijden van de adhan en de iqama" src="images/dashboards/prayer-times-card-light.jpg" width="600">
</picture>

Het volgende gebed is vet en de gebeden die voorbij zijn, zijn grijs. Vóór Fajr toont de kaart de tijden van de dag die begint.

Vervang de entiteit-ID's bovenaan de kaart door de jouwe, zie [Entiteit-ID's](../README.nl.md#entiteit-ids). Publiceert je moskee geen foto, verwijder dan de kaart `picture-entity`. Publiceert ze geen iqama's, dan toont de kolom Iqama `–`.

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: image.my_mosque_picture
    show_name: false
    show_state: false
    aspect_ratio: "2:1"
  - type: markdown
    content: |-
      {%- set prayers = {
        'fajr': ['sensor.my_mosque_fajr_prayer', 'sensor.my_mosque_fajr_iqama'],
        'shuruq': ['sensor.my_mosque_shuruq', none],
        'dhuhr': ['sensor.my_mosque_dhuhr_prayer', 'sensor.my_mosque_dhuhr_iqama'],
        'asr': ['sensor.my_mosque_asr_prayer', 'sensor.my_mosque_asr_iqama'],
        'maghrib': ['sensor.my_mosque_maghrib_prayer', 'sensor.my_mosque_maghrib_iqama'],
        'isha': ['sensor.my_mosque_isha_prayer', 'sensor.my_mosque_isha_iqama'],
      } %}
      {%- set next_name = 'sensor.my_mosque_next_salat_name' %}
      {%- set next_time = 'sensor.my_mosque_next_salat_time' %}
      {%- set hijri_day = 'sensor.my_mosque_hijri_day' %}
      {%- set hijri_month = 'sensor.my_mosque_hijri_month' %}
      {%- set hijri_year = 'sensor.my_mosque_hijri_year' %}
      {%- macro hm(entity) -%}
      {{ as_timestamp(states(entity), none) | timestamp_custom('%H:%M', default='–') if entity else '' }}
      {%- endmacro %}
      {%- set next = states(next_name) %}
      {%- set left = (as_timestamp(states(next_time), 0) - as_timestamp(now())) | int(0) %}
      ## {{ device_attr(device_id(next_name), 'name') }}
      <ha-icon icon="mdi:star-crescent"></ha-icon> {{ states(hijri_day) }} {{ state_translated(hijri_month) }} {{ states(hijri_year) }}

      <ha-alert alert-type="success" title="{{ state_translated(next_name) }} · {{ hm(next_time) }}">over {{ left // 3600 }} h {{ '%02d' | format(left % 3600 // 60) }} min</ha-alert>

      | | Adhan | Iqama |
      |:--|:-:|:-:|
      {% for key, (adhan, iqama) in prayers.items() -%}
      {% set cells = [key | title, hm(next_time if key == next else adhan), hm(iqama)] -%}
      {% if key == next -%}
      | **{{ cells | join('** | **') }}** |
      {% elif as_timestamp(states(adhan), 0) < as_timestamp(now()) -%}
      | <font color="gray">{{ cells | join('</font> | <font color="gray">') }}</font> |
      {% else -%}
      | {{ cells | join(' | ') }} |
      {% endif -%}
      {% endfor %}
```

## Volgend gebed

```yaml
type: markdown
text_only: true
content: |-
  {%- set next_name = 'sensor.my_mosque_next_salat_name' %}
  {%- set next_time = 'sensor.my_mosque_next_salat_time' %}
  {%- set left = (as_timestamp(states(next_time), 0) - as_timestamp(now())) | int(0) %}
  <ha-alert alert-type="info" title="{{ state_translated(next_name) }} · {{ as_timestamp(states(next_time), 0) | timestamp_custom('%H:%M') }}">over {{ left // 3600 }} h {{ '%02d' | format(left % 3600 // 60) }} min</ha-alert>
```

Vervang de twee entiteit-ID's door de jouwe.

## Moskeescherm

<img alt="Moskeescherm met een grote klok, de Hijri-datum en de zes gebedstijden op de foto van de moskee" src="images/dashboards/mosque-display-tablet.jpg" width="640"> <img alt="Moskeescherm op een telefoon" src="images/dashboards/mosque-display-phone.jpg" width="180">

De klok, de datum van vandaag en de Hijri-datum, en de zes tijden van de dag met hun iqama, op de foto van je moskee. Het volgende gebed is paars, en tussen de adhan en de iqama telt het scherm af tot de iqama. Op vrijdag wordt Dhuhr vervangen door Jumu'a als je moskee die publiceert. De namen van de gebeden zijn in de taal van Home Assistant.

Er zijn geen entiteit-ID's te vervangen: de kaart vindt de entiteiten van je moskee zelf. Volg je meerdere moskeeën, zet `mosque` dan op de naam van het apparaat van de moskee die je wilt tonen.

1. Installeer **button-card** met HACS: open **HACS**, zoek naar **button-card**, kies **Downloaden** en herlaad daarna de pagina in je browser. Versie 7 vereist Home Assistant 2025.10 of nieuwer; de kaart is getest met versie 7.0.1.
2. Open je dashboard, kies ✏️ **Dashboard bewerken** en daarna ➕ om een weergave toe te voegen. Kies bij **Indeling** **Paneel (één kaart)** en kies **Opslaan**.
3. Voeg in de nieuwe weergave een kaart **Handmatig** toe, plak de YAML hieronder en kies **Opslaan**.

```yaml
type: custom:button-card
variables:
  # The name of the mosque device, if you follow several mosques.
  mosque: ""
  # The entities of the mosque, found by their translation key: nothing to replace.
  entities: |
    [[[
      const own = Object.values(hass.entities).filter((e) => e.platform === "mawaqit");
      const device = variables.mosque
        ? Object.values(hass.devices).find((d) => [d.name_by_user, d.name].includes(variables.mosque))
        : hass.devices[own[0]?.device_id];
      if (!device) return undefined;
      return {
        name: device.name_by_user || device.name,
        ...Object.fromEntries(
          own.filter((e) => e.device_id === device.id).map((e) => [e.translation_key, e.entity_id])
        ),
      };
    ]]]
  # The prayers of the day, with their status: past, active (until the iqama) or next.
  prayers: |
    [[[
      const ids = variables.entities ?? {};
      const time = (key) => {
        const state = states[ids[key]]?.state;
        return state && !["unknown", "unavailable"].includes(state) ? new Date(state) : undefined;
      };
      const now = new Date();
      const nextKey = states[ids.next_salat_name]?.state;
      const nextTime = time("next_salat_time");
      const label = (key) =>
        states[ids.next_salat_name] ? helpers.localize(states[ids.next_salat_name], key) : key;
      // Jumu'a replaces Dhuhr on Fridays, when the mosque publishes it.
      const jumua = time("prayer_jumua");
      const isJumua = jumua && jumua.toDateString() === now.toDateString();
      const prayers = [
        ["fajr", "الفجر", "mdi:weather-sunset-up"],
        ["shuruq", "الشروق", "mdi:weather-sunset"],
        ["dhuhr", "الظهر", "mdi:weather-sunny"],
        ["asr", "العصر", "mdi:sun-angle-outline"],
        ["maghrib", "المغرب", "mdi:weather-sunset-down"],
        ["isha", "العشاء", "mdi:weather-night"],
      ].map(([key, ar, icon]) => {
        let adhan = time(`prayer_${key}`);
        let iqama = time(`iqama_${key}`);
        // After Isha the sensors still show today's Fajr: show the next one.
        if (key === nextKey && nextTime && adhan && nextTime - adhan > 12 * 3600e3) {
          if (iqama) iqama = new Date(iqama.getTime() + (nextTime - adhan));
          adhan = nextTime;
        }
        let name = label(key);
        if (key === "dhuhr" && isJumua) {
          [name, ar, adhan, iqama] = ["Jumu'a", "الجمعة", jumua, undefined];
        }
        let status = "";
        if (adhan && iqama && adhan <= now && now < iqama) status = "active";
        else if (key === nextKey) status = "next";
        else if ((iqama ?? adhan) < now) status = "past";
        return { name, ar, icon, adhan, iqama, status };
      });
      const active = prayers.find((p) => p.status === "active");
      const countdown = active
        ? { title: `Iqama · ${active.name}`, until: active.iqama }
        : nextKey && nextTime && { title: label(nextKey), until: nextTime };
      return { prayers, active: !!active, countdown };
    ]]]
update_timer: 1000
show_name: false
show_icon: false
show_state: false
tap_action:
  action: none
styles:
  card:
    - height: calc(100vh - var(--header-height, 56px))
    - min-height: 480px
    - padding: clamp(16px, 3vw, 40px)
    - box-sizing: border-box
    - border: none
    - border-radius: 0
    - color: white
    - font-variant-numeric: tabular-nums
    - background: |
        [[[
          const url = states[variables.entities?.picture]?.attributes.entity_picture;
          const shade =
            "radial-gradient(ellipse at 50% 40%, rgba(22, 8, 40, 0.35), rgba(22, 8, 40, 0.85) 70%), " +
            "linear-gradient(180deg, rgba(22, 8, 40, 0.55), rgba(22, 8, 40, 0.2) 35%, rgba(22, 8, 40, 0.92))";
          return url ? `${shade}, center / cover no-repeat url("${url}") #14081f` : `${shade}, #14081f`;
        ]]]
  grid:
    - grid-template-areas: '"header" "clock" "tiles" "flash"'
    - grid-template-rows: auto 1fr auto auto
    - grid-template-columns: 1fr
    - row-gap: 2vh
    - height: 100%
# Each field is redrawn only when its content changes: the clock every second, the rest rarely.
custom_fields:
  header: |
    [[[
      const ids = variables.entities;
      if (!ids) return `<div class="empty">MAWAQIT: mosque not found</div>`;
      const escape = (text) => String(text).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
      const logo = states[ids.logo]?.attributes.entity_picture;
      const day = states[ids.hijri_day]?.state;
      const hijri = /^\d+$/.test(day)
        ? `${day} ${helpers.localize(states[ids.hijri_month])} ${states[ids.hijri_year]?.state ?? ""}`
        : "";
      return `
        <header>
          <div class="mosque">
            ${logo ? `<img src="${logo}" alt="">` : `<ha-icon icon="mdi:mosque"></ha-icon>`}
            <span>${escape(ids.name)}</span>
          </div>
          <div class="brand">
            <img src="https://brands.home-assistant.io/mawaqit/dark_icon.png" alt="">
            <span>MAWAQIT</span>
          </div>
          <div class="dates">
            <div>${helpers.formatDateWeekdayDay(new Date())}</div>
            <div class="hijri">${hijri}</div>
          </div>
        </header>`;
    ]]]
  clock: |
    [[[
      const now = new Date();
      const pad = (n) => String(n).padStart(2, "0");
      const countdown = variables.prayers.countdown;
      let left = "";
      if (countdown) {
        const s = Math.max(0, Math.ceil((countdown.until - now) / 1000));
        const h = Math.floor(s / 3600);
        left = (h ? `${h}:` : "") + `${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}`;
      }
      return `
        <div class="clock">${helpers.formatTime(now)}<span>${pad(now.getSeconds())}</span></div>
        ${countdown ? `<div class="countdown"><b>${countdown.title}</b><span>−${left}</span></div>` : ""}`;
    ]]]
  tiles: |
    [[[
      const { prayers, active } = variables.prayers;
      const hm = (date) => (date ? helpers.formatTime(date) : "—");
      return `
        <div class="tiles ${active ? "has-active" : ""}">
          ${prayers.map((p) => `
            <div class="tile ${p.status}">
              <ha-icon icon="${p.icon}"></ha-icon>
              <div class="name">${p.name}</div>
              <div class="ar">${p.ar}</div>
              <div class="adhan">${hm(p.adhan)}</div>
              <div class="iqama">${p.iqama ? hm(p.iqama) : "&nbsp;"}</div>
            </div>`).join("")}
        </div>`;
    ]]]
  # The flash message scrolls at a pace set by the clock, so redrawing it every second does not restart it.
  flash: |
    [[[
      const flash = states[variables.entities?.flash_message];
      if (!flash || ["unknown", "unavailable"].includes(flash.state)) return "";
      const escape = (text) => String(text).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
      const seconds = Math.max(15, flash.state.length / 3);
      const delay = -((Date.now() / 1000) % seconds);
      const dir = flash.attributes.direction === "rtl" ? "rtl" : "ltr";
      const color = /^#[0-9a-f]{3,8}$/i.test(flash.attributes.color) ? flash.attributes.color : "#490094";
      return `
        <div class="flash" style="background: ${color}">
          <span dir="${dir}" class="${dir}" style="animation-duration: ${seconds}s; animation-delay: ${delay}s">${escape(flash.state)}</span>
        </div>`;
    ]]]
extra_styles: |
  #header, #clock, #tiles, #flash { text-align: left; min-width: 0; }
  header { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 16px; }
  .mosque { display: flex; align-items: center; gap: 14px; font-size: clamp(18px, 2.2vw, 30px); font-weight: 500; }
  .mosque img { height: clamp(40px, 5vw, 64px); width: clamp(40px, 5vw, 64px); object-fit: contain; border-radius: 50%; background: white; padding: 4px; box-sizing: border-box; }
  .mosque ha-icon { --mdc-icon-size: clamp(32px, 4vw, 48px); color: #c9a2ff; }
  .brand { display: flex; align-items: center; gap: 10px; font-size: clamp(13px, 1.3vw, 18px); font-weight: 600; letter-spacing: 0.2em; opacity: 0.9; }
  .brand img { height: clamp(28px, 3vw, 40px); width: auto; }
  .dates { justify-self: end; text-align: right; font-size: clamp(14px, 1.6vw, 22px); opacity: 0.9; }
  .dates .hijri { color: #c9a2ff; font-weight: 500; }
  #clock { display: flex; flex-direction: column; align-items: center; justify-content: center; text-shadow: 0 2px 24px rgba(0, 0, 0, 0.5); }
  .clock { font-size: clamp(72px, 15vw, 220px); font-weight: 200; line-height: 1; letter-spacing: -0.02em; }
  .clock span { font-size: 0.3em; font-weight: 300; margin-left: 0.15em; opacity: 0.7; }
  .countdown { margin-top: 2vh; display: flex; gap: 0.6em; align-items: baseline; font-size: clamp(20px, 2.8vw, 40px);
    padding: 0.35em 1em; border-radius: 999px; background: rgba(22, 8, 40, 0.55); border: 1px solid rgba(167, 99, 247, 0.7);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }
  .countdown b { color: #c9a2ff; font-weight: 500; }
  .tiles { display: grid; grid-template-columns: repeat(6, 1fr); gap: clamp(8px, 1.2vw, 18px); }
  .tile {
    display: flex; flex-direction: column; align-items: center; gap: 0.2em;
    padding: clamp(10px, 1.6vw, 22px) 6px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
  }
  .tile ha-icon { --mdc-icon-size: clamp(20px, 2vw, 28px); opacity: 0.8; }
  .tile .name { font-size: clamp(14px, 1.5vw, 22px); font-weight: 500; }
  .tile .ar { font-size: clamp(13px, 1.3vw, 19px); opacity: 0.7; }
  .tile .adhan { font-size: clamp(24px, 3.2vw, 48px); font-weight: 300; }
  .tile .iqama { font-size: clamp(13px, 1.3vw, 19px); opacity: 0.75; }
  .tile.past { opacity: 0.45; }
  .tile.next, .tile.active {
    background: linear-gradient(160deg, rgba(167, 99, 247, 0.95), rgba(73, 0, 148, 0.95));
    border-color: rgba(201, 162, 255, 0.8);
    box-shadow: 0 10px 40px rgba(146, 60, 246, 0.45);
    transform: translateY(-6px);
  }
  .tile.active { box-shadow: 0 10px 60px rgba(146, 60, 246, 0.8); }
  .has-active .tile.next {
    background: rgba(167, 99, 247, 0.18);
    border-color: rgba(167, 99, 247, 0.9);
    box-shadow: none;
    transform: none;
  }
  .flash { overflow: hidden; white-space: nowrap; border-radius: 12px; padding: 0.4em 0; font-size: clamp(16px, 2vw, 28px);
    font-weight: 500; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4); }
  .flash span { display: inline-block; padding-left: 100%; animation: ticker linear infinite; }
  .flash span.rtl { animation-name: ticker-rtl; }
  @keyframes ticker { to { transform: translateX(-100%); } }
  @keyframes ticker-rtl { from { transform: translateX(-100%); } to { transform: translateX(0); } }
  .empty { display: grid; place-items: center; height: 100%; font-size: 32px; }
  @media (max-width: 700px) {
    header { grid-template-columns: 1fr; }
    .brand { grid-row: 1; }
    .dates { justify-self: start; text-align: left; }
    .tiles { grid-template-columns: repeat(3, 1fr); }
  }
```

Open de weergave op een wandtablet schermvullend in de browser, of gebruik [kiosk-mode](https://github.com/NemesisRE/kiosk-mode) om de kopbalk en de zijbalk te verbergen.
