/**
 * FitPulse SaaS Platform - Main Frontend JavaScript (Phase 1)
 * Handles interactive navigation, mobile menu, and interactive instant demo tools.
 */

function initFitPulse() {
  initMobileNavigation();
  initFoodAlternativesDemo();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initFitPulse);
} else {
  initFitPulse();
}

/**
 * Mobile Navigation Drawer & Toggle
 */
function initMobileNavigation() {
  const toggleBtn = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener('click', () => {
      const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
      toggleBtn.setAttribute('aria-expanded', !isExpanded);
      
      if (!isExpanded) {
        navLinks.style.display = 'flex';
        navLinks.style.flexDirection = 'column';
        navLinks.style.position = 'absolute';
        navLinks.style.top = 'var(--nav-height)';
        navLinks.style.left = '0';
        navLinks.style.right = '0';
        navLinks.style.background = 'rgba(9, 13, 22, 0.98)';
        navLinks.style.padding = '1.5rem';
        navLinks.style.borderBottom = '1px solid var(--border)';
      } else {
        navLinks.style.display = '';
        navLinks.style.position = '';
      }
    });
  }
}

/**
 * Interactive Instant Demo for Free Food Alternative Tool
 * Allows visitors to test search and quick chips right on the landing page
 */
function initFoodAlternativesDemo() {
  const searchInput = document.getElementById('foodSearchInput');
  const searchBtn = document.getElementById('foodSearchBtn');
  const resultCard = document.getElementById('demoResultCard');
  const chips = document.querySelectorAll('.filter-chip');

  // Built-in database of instant demo alternatives
  const alternativesDatabase = {
    burger: {
      original: "Fast Food Beef Burger",
      alternative: "Grilled Turkey / Lean Beef Patties on Whole Grain Thins",
      calories: "340 kcal (vs 680 kcal)",
      protein: "38g Protein",
      carbs: "26g Complex Carbs",
      fat: "8g Healthy Fats",
      explanation: "Using lean 93/7 minced turkey or extra-lean grass-fed beef, seasoned with smoked paprika and garlic, served with crisp lettuce, sliced tomato, and light yogurt-dijon sauce eliminates excess saturated oil while doubling bioavailable protein.",
      prepTime: "12 mins"
    },
    pizza: {
      original: "Delivery Pepperoni Pizza (3 slices)",
      alternative: "High-Protein Greek Yogurt Crust Pizza with Chicken Breast",
      calories: "410 kcal (vs 920 kcal)",
      protein: "44g Protein",
      carbs: "34g Carbs",
      fat: "9g Fats",
      explanation: "A 2-ingredient crust made from self-rising flour and non-fat plain Greek yogurt baked crisp with crushed Italian plum tomatoes, part-skim mozzarella, and grilled shredded chicken breast.",
      prepTime: "18 mins"
    },
    "fried chicken": {
      original: "Deep Fried Crispy Chicken",
      alternative: "Air-Crisped Cornflake-Crusted Chicken Tenderloins",
      calories: "290 kcal (vs 580 kcal)",
      protein: "42g Protein",
      carbs: "18g Carbs",
      fat: "4g Fats",
      explanation: "Chicken breast tenders dredged in whipped egg whites, coated in crushed whole-grain cornflakes or panko, and air-fried at 200°C for 12 minutes yields the identical satisfying crunch with 70% less fat.",
      prepTime: "15 mins"
    },
    "ice cream": {
      original: "Premium Dairy Ice Cream (1 Pint)",
      alternative: "Whipped Cottage Cheese & Frozen Berry Soft-Serve",
      calories: "180 kcal (vs 640 kcal)",
      protein: "24g Protein",
      carbs: "16g Carbs",
      fat: "2g Fats",
      explanation: "Blending low-fat cottage cheese with frozen wild blueberries, pure vanilla extract, and a pinch of stevia produces a rich, velvety soft-serve texture packed with slow-digesting casein protein.",
      prepTime: "4 mins"
    },
    chips: {
      original: "Commercial Fried Potato Chips",
      alternative: "Seasoned Baked Air-Dried Zucchini & Sweet Potato Crisps",
      calories: "120 kcal (vs 320 kcal)",
      protein: "4g Protein",
      carbs: "22g Carbs",
      fat: "2g Fats",
      explanation: "Thinly mandoline-sliced sweet potato or zucchini tossed lightly in avocado oil spray and sea salt, baked low and slow for a crisp snack with sustained low-glycemic energy.",
      prepTime: "20 mins"
    },
    "soft drinks": {
      original: "Regular Sugary Soda (12 oz)",
      alternative: "Sparkling Mineral Water with Fresh Citrus & Crushed Mint",
      calories: "5 kcal (vs 150 kcal)",
      protein: "0g Protein",
      carbs: "1g Carbs",
      fat: "0g Fats",
      explanation: "Chilled effervescent sparkling water infused with fresh key lime juice, squeezed blood orange, and muddled mint leaves satisfies carbonation cravings with zero refined fructose syrups.",
      prepTime: "2 mins"
    }
  };

  function displayAlternative(query) {
    if (!resultCard) return;
    const cleanQuery = query.trim().toLowerCase();
    
    // Find closest match or default to burger
    let matchKey = Object.keys(alternativesDatabase).find(key => cleanQuery.includes(key));
    if (!matchKey) {
      matchKey = 'burger';
    }
    
    const data = alternativesDatabase[matchKey];
    
    resultCard.innerHTML = `
      <div class="result-header">
        <div>
          <span style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Standard Craving</span>
          <div style="color: var(--danger); font-weight: 600; text-decoration: line-through;">${data.original}</div>
        </div>
        <div style="text-align: right;">
          <span style="font-size: 0.75rem; color: var(--primary); font-weight: 700; text-transform: uppercase;">Smart Alternative</span>
          <div class="result-item-name" style="color: var(--primary);">${data.alternative}</div>
        </div>
      </div>
      
      <div class="nutrition-pill-grid">
        <div class="nutri-col">
          <div class="nutri-val calories">${data.calories}</div>
          <div class="nutri-lbl">Estimated Energy</div>
        </div>
        <div class="nutri-col">
          <div class="nutri-val">${data.protein}</div>
          <div class="nutri-lbl">Bioavailable Protein</div>
        </div>
        <div class="nutri-col">
          <div class="nutri-val" style="color: var(--accent-cyan);">${data.carbs}</div>
          <div class="nutri-lbl">Carbohydrates</div>
        </div>
        <div class="nutri-col">
          <div class="nutri-val" style="color: var(--secondary);">${data.fat}</div>
          <div class="nutri-lbl">Total Fats</div>
        </div>
      </div>
      
      <p class="result-explanation">
        <strong>Preparation & Nutritional Logic:</strong> ${data.explanation}
      </p>
      
      <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.8rem; color: var(--text-muted); border-top: 1px solid var(--border); padding-top: 0.75rem;">
        <span>Prep Time: ~${data.prepTime}</span>
        <span style="color: var(--primary); font-weight: 600;">100% Free Public Tool</span>
      </div>
    `;
  }

  // Handle Chips click
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const val = chip.getAttribute('data-value');
      if (searchInput) searchInput.value = val;
      displayAlternative(val);
    });
  });

  // Handle Search Input & Button
  if (searchBtn && searchInput) {
    searchBtn.addEventListener('click', () => {
      displayAlternative(searchInput.value || 'burger');
    });
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        displayAlternative(searchInput.value || 'burger');
      }
    });
  }
}
