export function showLoader() {
  const loader = document.getElementById("loading-indicator");
  if (loader) loader.style.display = 'block';
}

export function hideLoader() {
  const loader = document.getElementById("loading-indicator");
  if (loader) loader.style.display = 'none';
}

