// Main JavaScript file for TourCompanyDB

document.addEventListener('DOMContentLoaded', function () {
  // Search Functionality for Staff Portal (Dashboard / Table List)
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', function (e) {
      const searchTerm = e.target.value.toLowerCase();
      const items = document.querySelectorAll('.searchable-item');

      items.forEach(function (item) {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
          item.style.display = ''; // Reverts to default display (flex/block/table-row)
        } else {
          item.style.display = 'none';
        }
      });
    });
  }
});