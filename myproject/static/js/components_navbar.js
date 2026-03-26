document.addEventListener('DOMContentLoaded', function () {
    const profileBtn = document.getElementById('profile-btn');
    const profileMenu = document.getElementById('profileMenu');
    if (profileBtn && profileMenu) {
      profileBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        profileMenu.classList.toggle('show');
      });
      document.addEventListener('click', function () {
        profileMenu.classList.remove('show');
      });
    }
  });