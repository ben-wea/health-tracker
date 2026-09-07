const searchInput = document.getElementById("food-search");
const resultsList = document.getElementById("search-results");
const statusLine = document.getElementById("search-status");
const addForm = document.getElementById("add-form");

let debounceTimer = null;

const fields = {
  fdc_id: document.getElementById("f-fdc-id"),
  description: document.getElementById("f-description"),
  calories: document.getElementById("f-calories"),
  protein: document.getElementById("f-protein"),
  carbs: document.getElementById("f-carbs"),
  fat: document.getElementById("f-fat"),
};

searchInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  const query = searchInput.value.trim();

  if (query.length < 2) {
    resultsList.innerHTML = "";
    statusLine.textContent = "";
    return;
  }

  debounceTimer = setTimeout(() => runSearch(query), 400);
});

async function runSearch(query) {
  statusLine.textContent = "Searching\u2026";
  resultsList.innerHTML = "";

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();

    if (data.error) {
      statusLine.textContent = data.error;
      return;
    }
    if (data.foods.length === 0) {
      statusLine.textContent = "No foods found.";
      return;
    }

    statusLine.textContent = "";
    data.foods.forEach(renderResult);
  } catch (err) {
    statusLine.textContent = "Search failed. Check your connection.";
  }
}

function renderResult(food) {
  const li = document.createElement("li");
  li.className = "result";

  const name = document.createElement("span");
  name.className = "result-name";
  name.textContent = food.description;

  const macros = document.createElement("span");
  macros.className = "result-macros";
  macros.textContent = `${Math.round(food.calories_per_100g)} kcal / 100g`;

  li.append(name, macros);
  li.addEventListener("click", () => selectFood(food));
  resultsList.appendChild(li);
}

function selectFood(food) {
  fields.fdc_id.value = food.fdc_id ?? "";
  fields.description.value = food.description;
  fields.calories.value = food.calories_per_100g;
  fields.protein.value = food.protein_per_100g;
  fields.carbs.value = food.carbs_per_100g;
  fields.fat.value = food.fat_per_100g;

  document.getElementById("selected-name").textContent = food.description;
  addForm.hidden = false;
  resultsList.innerHTML = "";
  statusLine.textContent = "";
}

addForm.addEventListener("submit", () => {
  const button = addForm.querySelector("button[type=submit]");
  button.disabled = true;
  button.textContent = "Adding\u2026";
});