document.addEventListener('DOMContentLoaded', function() {
  const toggleBtn = document.getElementById('toggleBtn');
  const sidebar = document.querySelector('.sidebar');
  const mainSection = document.getElementById('main');

  if (toggleBtn && sidebar && mainSection) {
    toggleBtn.addEventListener('click', function() {
      sidebar.classList.toggle('collapsed');
      mainSection.classList.toggle('full-width');
    });
  }
});