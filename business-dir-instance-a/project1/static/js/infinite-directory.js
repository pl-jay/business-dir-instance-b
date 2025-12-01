(function () {
  const grid = document.getElementById('grid');
  const sentinel = document.getElementById('sentinel');
  const err = document.getElementById('err');
  const retry = document.getElementById('retry');
  const filterForm = document.getElementById('filterForm');

  if (!grid || !sentinel) return;

  // Maintain query params
  const url = new URL(window.location.href);
  let page = Number(url.searchParams.get('page') || 1);
  let loading = false;
  let done = false;

  // Replace pagination with API endpoint; server sends JSON for next pages
function apiUrl(nextPage) {
  const u = new URL(window.location.origin + window.DIR_API_URL);
  // copy filters/sort from current URL (but not page)
  const current = new URL(window.location.href);
  current.searchParams.forEach((v, k) => { if (k !== 'page') u.searchParams.set(k, v); });
  u.searchParams.set('page', String(nextPage));
  return u.toString();
}


  function injectSkeletons(n = 6) {
    const frag = document.createDocumentFragment();
    for (let i = 0; i < n; i++) {
      const col = document.createElement('div');
      col.className = 'col-12 col-sm-6 col-lg-4';
      col.innerHTML = `
        <div class="card h-100 p-3">
          <div class="skel" style="height:18px;width:70%;margin-bottom:.5rem;"></div>
          <div class="skel" style="height:12px;width:40%;margin-bottom:.75rem;"></div>
          <div class="skel" style="height:12px;width:95%;margin-bottom:.3rem;"></div>
          <div class="skel" style="height:12px;width:80%;"></div>
        </div>`;
      col.dataset.skeleton = '1';
      frag.appendChild(col);
    }
    grid.appendChild(frag);
  }

  function removeSkeletons() {
    grid.querySelectorAll('[data-skeleton="1"]').forEach(n => n.remove());
  }

  async function loadMore() {
    if (loading || done) return;
    loading = true; err.classList.add('d-none');
    injectSkeletons();

    try {
      const res = await fetch(apiUrl(page + 1), { headers: { 'Accept': 'application/json' } });
      if (!res.ok) throw new Error('Bad status ' + res.status);
      const data = await res.json();

if (data.page <= page) {
  removeSkeletons();
  // prevent any further loads to avoid infinite duplicate appends
  done = true;
  return;
}
console.debug("Loaded page", data.page, "has_next:", data.has_next);

      // Append HTML of cards returned by API
      grid.insertAdjacentHTML('beforeend', data.html);

      // Update URL (so back/forward works) without full reload
      page = data.page;
      const current = new URL(window.location.href);
      current.searchParams.set('page', page);
      window.history.replaceState({}, '', current);

      if (!data.has_next) done = true;
    } catch (e) {
      removeSkeletons();
      err.classList.remove('d-none');
    } finally {
      loading = false;
    }
  }

  // Retry button
  if (retry) retry.addEventListener('click', loadMore);

  // Observe sentinel
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) loadMore();
      });
    }, { rootMargin: '600px 0px' }); // prefetch ahead
    io.observe(sentinel);
  } // else: fallback button remains visible

  // Submit filters without losing scroll; push state
  if (filterForm) {
    filterForm.addEventListener('submit', (e) => {
      // let the server render page 1 (SEO) – we do a normal navigation
      // Optional enhancement: do AJAX and replace grid, then reset page=1.
    });
  }

  // Global from template (set in block below)
})();
