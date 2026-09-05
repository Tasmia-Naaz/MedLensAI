document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  const loginEmail = document.getElementById('loginEmail');
  const loginPassword = document.getElementById('loginPassword');
  const loginBtn = document.getElementById('loginBtn');
  const loginSpinner = document.getElementById('loginSpinner');
  const loginAlert = document.getElementById('loginAlert');
  const fillDemoBtn = document.getElementById('fillDemoBtn');

  // Fast Demo Fill
  if (fillDemoBtn) {
    fillDemoBtn.addEventListener('click', () => {
      loginEmail.value = 'demo@medlens.com';
      loginPassword.value = 'demo123';
      loginForm.dispatchEvent(new Event('submit'));
    });
  }

  // Handle Login Submission
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      loginAlert.classList.add('d-none');

      const email = loginEmail.value.trim();
      const password = loginPassword.value.trim();

      if (!email || !password) {
        loginAlert.textContent = 'Please provide both email and password.';
        loginAlert.classList.remove('d-none');
        return;
      }

      loginBtn.disabled = true;
      loginSpinner.classList.remove('d-none');

      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (res.ok && data.success) {
          window.location.href = data.redirect || '/dashboard';
        } else {
          loginAlert.textContent = data.message || 'Login failed. Please verify credentials.';
          loginAlert.classList.remove('d-none');
          loginBtn.disabled = false;
          loginSpinner.classList.add('d-none');
        }
      } catch (err) {
        loginAlert.textContent = 'Network error during login. Please try again.';
        loginAlert.classList.remove('d-none');
        loginBtn.disabled = false;
        loginSpinner.classList.add('d-none');
      }
    });
  }

  // Handle Registration Submission
  const registerForm = document.getElementById('registerForm');
  const regName = document.getElementById('regName');
  const regEmail = document.getElementById('regEmail');
  const regPassword = document.getElementById('regPassword');
  const regConfirmPassword = document.getElementById('regConfirmPassword');
  const regSubmitBtn = document.getElementById('regSubmitBtn');
  const regSpinner = document.getElementById('regSpinner');
  const registerAlert = document.getElementById('registerAlert');

  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      registerAlert.classList.add('d-none');

      const name = regName.value.trim();
      const email = regEmail.value.trim();
      const password = regPassword.value.trim();
      const confirmPassword = regConfirmPassword.value.trim();

      if (!name || !email || !password) {
        registerAlert.textContent = 'All fields are required.';
        registerAlert.classList.remove('d-none');
        return;
      }

      if (password !== confirmPassword) {
        registerAlert.textContent = 'Passwords do not match.';
        registerAlert.classList.remove('d-none');
        return;
      }

      if (password.length < 6) {
        registerAlert.textContent = 'Password must be at least 6 characters.';
        registerAlert.classList.remove('d-none');
        return;
      }

      regSubmitBtn.disabled = true;
      regSpinner.classList.remove('d-none');

      try {
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password })
        });

        const data = await res.json();

        if (res.ok && data.success) {
          window.location.href = data.redirect || '/dashboard';
        } else {
          registerAlert.textContent = data.message || 'Registration failed.';
          registerAlert.classList.remove('d-none');
          regSubmitBtn.disabled = false;
          regSpinner.classList.add('d-none');
        }
      } catch (err) {
        registerAlert.textContent = 'Network error during registration.';
        registerAlert.classList.remove('d-none');
        regSubmitBtn.disabled = false;
        regSpinner.classList.add('d-none');
      }
    });
  }
});
