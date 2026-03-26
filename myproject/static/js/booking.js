function changeCount(type, delta) {
  const displayId = type === 'adults' ? 'adults-display' : 'children-display';
  const hiddenId = type === 'adults' ? 'num_adults' : 'num_children';
  const el = document.getElementById(displayId);
  const hidden = document.getElementById(hiddenId);
  let current = parseInt(el.textContent);
  current = Math.max(0, current + delta);
  if (type === 'adults') current = Math.max(1, current);
  el.textContent = current;
  hidden.value = current;
}