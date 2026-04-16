const categoryInput = document.querySelector("#categoryInput");
const locationInput = document.querySelector("#locationInput");
const audienceInput = document.querySelector("#audienceInput");
const topicInput = document.querySelector("#topicInput");
const budgetInput = document.querySelector("#budgetInput");
const loadPlanButton = document.querySelector("#loadPlanButton");
const planStatus = document.querySelector("#planStatus");

const summaryText = document.querySelector("#summaryText");
const venueText = document.querySelector("#venueText");
const attendanceText = document.querySelector("#attendanceText");
const gtmTipText = document.querySelector("#gtmTipText");

const sponsorList = document.querySelector("#sponsorList");
const speakerList = document.querySelector("#speakerList");
const pricingList = document.querySelector("#pricingList");
const venueList = document.querySelector("#venueList");
const gtmList = document.querySelector("#gtmList");

function decodeText(value) {
  if (typeof value !== "string") return value;
  return value
    .replace(/â€™/g, "'")
    .replace(/â€œ/g, '"')
    .replace(/â€\x9d/g, '"')
    .replace(/â€"/g, '"');
}

function createMetaChips(items) {
  const wrapper = document.createElement("div");
  wrapper.className = "stack-meta";
  items.forEach((item) => {
    if (!item) return;
    const chip = document.createElement("span");
    chip.className = "meta-chip";
    chip.textContent = decodeText(String(item));
    wrapper.appendChild(chip);
  });
  return wrapper;
}

function setEmptyState(target, message) {
  target.className = "stack-list empty-state";
  target.textContent = message;
}

function renderSponsors(sponsors = []) {
  sponsorList.innerHTML = "";
  sponsorList.className = "stack-list";
  if (!sponsors.length) return setEmptyState(sponsorList, "No sponsor recommendations found.");

  sponsors.forEach((sponsor) => {
    const card = document.createElement("article");
    card.className = "stack-item";
    card.appendChild(createMetaChips([sponsor.industry, `Score ${sponsor.relevance_score}`]));
    card.innerHTML += `<h3>${decodeText(sponsor.name)}</h3><p>${decodeText(sponsor.reason || "")}</p>`;
    sponsorList.appendChild(card);
  });
}

function renderSpeakers(speakers = []) {
  speakerList.innerHTML = "";
  speakerList.className = "stack-list";
  if (!speakers.length) return setEmptyState(speakerList, "No speaker recommendations found.");

  speakers.forEach((speaker) => {
    const card = document.createElement("article");
    card.className = "stack-item";
    card.appendChild(createMetaChips([speaker.expertise]));
    card.innerHTML += `<h3>${decodeText(speaker.name)}</h3><p><strong>Topic:</strong> ${decodeText(speaker.suggested_topic || "")}</p><p>${decodeText(speaker.why || "")}</p>`;
    speakerList.appendChild(card);
  });
}

function renderPricing(pricing = {}) {
  pricingList.innerHTML = "";
  pricingList.className = "stack-list";
  if (!Object.keys(pricing).length) return setEmptyState(pricingList, "No pricing strategy found.");

  const card = document.createElement("article");
  card.className = "stack-item";
  card.appendChild(
    createMetaChips([
      `Early bird INR ${pricing.early_bird ?? "-"}`,
      `General INR ${pricing.general ?? "-"}`,
      `VIP INR ${pricing.vip ?? "-"}`,
      `Attendance ${pricing.expected_attendance ?? "-"}`,
    ])
  );
  card.innerHTML += `<h3>Pricing recommendation</h3><p>${decodeText(pricing.reasoning || "")}</p>`;
  pricingList.appendChild(card);
}

function renderVenues(venues = []) {
  venueList.innerHTML = "";
  venueList.className = "stack-list";
  if (!venues.length) return setEmptyState(venueList, "No venue recommendations found.");

  venues.forEach((venue) => {
    const card = document.createElement("article");
    card.className = "stack-item";
    card.appendChild(createMetaChips([venue.city, `Capacity ${venue.capacity}`, venue.estimated_cost]));
    card.innerHTML += `<h3>${decodeText(venue.name)}</h3><p>${decodeText(venue.why || "")}</p>`;
    venueList.appendChild(card);
  });
}

function renderGtm(gtm = {}) {
  gtmList.innerHTML = "";
  gtmList.className = "stack-list";
  if (!Object.keys(gtm).length) return setEmptyState(gtmList, "No GTM strategy found.");

  const card = document.createElement("article");
  card.className = "stack-item";
  card.innerHTML = `
    <h3>Promotion message</h3>
    <p>${decodeText(gtm.promotion_message || "No message provided.")}</p>
    <div class="stack-meta"></div>
    <p><strong>Discord:</strong> ${decodeText((gtm.discord_communities || []).join(", ")) || "None"}</p>
    <p><strong>LinkedIn:</strong> ${decodeText((gtm.linkedin_groups || []).join(", ")) || "None"}</p>
    <p><strong>Best channels:</strong> ${decodeText((gtm.best_channels || []).join(", ")) || "None"}</p>
  `;

  const metaContainer = card.querySelector(".stack-meta");
  (gtm.best_channels || []).forEach((channel) => {
    const chip = document.createElement("span");
    chip.className = "meta-chip";
    chip.textContent = decodeText(channel);
    metaContainer.appendChild(chip);
  });

  gtmList.appendChild(card);
}

function populateInputs(input = {}) {
  if (input.category) categoryInput.value = input.category;
  if (input.location) locationInput.value = input.location;
  if (input.audience_size) audienceInput.value = input.audience_size;
  if (input.topic) topicInput.value = input.topic;
  if (input.budget) budgetInput.value = input.budget;
}

async function loadLatestPlan() {
  planStatus.textContent = "Loading latest conference_plan.json...";

  try {
    const response = await fetch("../conference_plan.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const outputs = data.agent_outputs || {};
    const finalPlan = data.final_plan || {};

    populateInputs(data.input || {});

    summaryText.textContent = decodeText(finalPlan.summary || "No summary available.");
    venueText.textContent = decodeText(finalPlan.recommended_venue || "No venue selected.");

    const insights = finalPlan.ml_insights || {};
    attendanceText.textContent = insights.predicted_attendance
      ? `${insights.predicted_attendance} attendees | ${decodeText(insights.confidence_score || "")}`
      : "No ML forecast available.";

    gtmTipText.textContent = decodeText(finalPlan.gtm_tip || "No GTM tip available.");

    renderSponsors(outputs.sponsors?.sponsors || []);
    renderSpeakers(outputs.speakers?.speakers || []);
    renderPricing(outputs.pricing?.pricing || {});
    renderVenues(outputs.venues?.venues || []);
    renderGtm(outputs.gtm?.gtm || outputs.gtm || {});

    planStatus.textContent = "Latest backend plan loaded successfully.";
  } catch (error) {
    planStatus.textContent = `Could not load conference_plan.json. Serve the repo root with a local web server and rerun the backend to refresh the plan. (${error.message})`;
    setEmptyState(sponsorList, "Plan not loaded yet.");
    setEmptyState(speakerList, "Plan not loaded yet.");
    setEmptyState(pricingList, "Plan not loaded yet.");
    setEmptyState(venueList, "Plan not loaded yet.");
    setEmptyState(gtmList, "Plan not loaded yet.");
  }
}

loadPlanButton.addEventListener("click", loadLatestPlan);

loadLatestPlan();
