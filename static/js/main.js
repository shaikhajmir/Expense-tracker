/* -------------------------
   THEME SWITCHER
--------------------------*/
const themeToggle = document.getElementById("themeToggle");
const themeIcon = document.getElementById("themeIcon");

// Load saved theme
let stored = localStorage.getItem("theme");
if (stored) {
  document.documentElement.setAttribute("data-theme", stored);
  themeIcon.className = stored === "dark"
    ? "bi bi-sun-fill"
    : "bi bi-moon-stars-fill";
}

themeToggle.addEventListener("click", () => {
  let current = document.documentElement.getAttribute("data-theme");
  let next = current === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);

  themeIcon.className = next === "dark"
    ? "bi bi-sun-fill"
    : "bi bi-moon-stars-fill";
});

/* -------------------------
   CHARTS
--------------------------*/

// Category Pie
if (typeof catLabels !== "undefined") {
  new Chart(document.getElementById("catChart"), {
    type: "pie",
    data: {
      labels: catLabels,
      datasets: [{
        data: catValues
      }]
    }
  });
}

// Monthly Bar Chart
if (typeof monthLabels !== "undefined") {
  new Chart(document.getElementById("monthChart"), {
    type: "bar",
    data: {
      labels: monthLabels,
      datasets: [{
        label: "Monthly Spending",
        data: monthValues
      }]
    }
  });
}

// password toggle
document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.getElementById('togglePwd');
  const pwd = document.getElementById('passwordInput');
  if (toggle && pwd) {
    toggle.addEventListener('click', function () {
      if (pwd.type === 'password') {
        pwd.type = 'text';
        toggle.innerHTML = '<i class="bi bi-eye-slash"></i>';
      } else {
        pwd.type = 'password';
        toggle.innerHTML = '<i class="bi bi-eye"></i>';
      }
    });
  }
});
// signup password toggle
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("toggleSignupPwd");
  const pwd = document.getElementById("passwordSignup");

  if (toggle && pwd) {
    toggle.addEventListener("click", () => {
      if (pwd.type === "password") {
        pwd.type = "text";
        toggle.innerHTML = '<i class="bi bi-eye-slash"></i>';
      } else {
        pwd.type = "password";
        toggle.innerHTML = '<i class="bi bi-eye"></i>';
      }
    });
  }
});
// Number counting animation for stats
document.addEventListener("DOMContentLoaded", () => {
  const counters = document.querySelectorAll(".stat-number");

  const animate = (counter) => {
    const target = +counter.getAttribute("data-value");
    let current = 0;
    const increment = target / 60;

    const update = () => {
      current += increment;
      if (current < target) {
        counter.innerText = Math.round(current);
        requestAnimationFrame(update);
      } else {
        counter.innerText = target;
      }
    };

    update();
  };

  counters.forEach(counter => animate(counter));
});
document.addEventListener("DOMContentLoaded", () => {
  const box = document.getElementById("coachMessages");
  if (box) {
    box.scrollTop = box.scrollHeight;
  }
});
