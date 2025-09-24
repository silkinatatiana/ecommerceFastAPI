function closeAllFilters() {
    document.querySelectorAll('.dropdown-filter-container').forEach(el => {
        el.classList.remove('active');
    });
}

document.querySelectorAll('.filter-trigger').forEach(trigger => {
    trigger.addEventListener('click', function(e) {
        const container = this.closest('.dropdown-filter-container');
        const isActive = container.classList.contains('active');
        closeAllFilters();
        if (!isActive) {
            container.classList.add('active');
        }
        e.stopPropagation();
    });
});

document.addEventListener('click', function(e) {
    if (!e.target.closest('.dropdown-filter-container')) {
        closeAllFilters();
    }
});

function filterDropdown(input, filterKey) {
    const container = input.closest('.dropdown-filter');
    const labels = container.querySelectorAll('.filter-options label');
    const query = input.value.toLowerCase();
    labels.forEach(label => {
        const text = label.textContent.toLowerCase();
        label.style.display = text.includes(query) ? '' : 'none';
    });
}

function applyFilters() {
    const params = new URLSearchParams();

    document.querySelectorAll('.dropdown-filter-container[data-filter]').forEach(container => {
        const filterName = container.dataset.filter;
        const checks = container.querySelectorAll('input[type="checkbox"]:checked');
        checks.forEach(ch => params.append(filterName, ch.value));
    });

    // Диапазоны
    const dateStart = document.querySelector('[name="date_start_filter"]').value;
    const dateEnd = document.querySelector('[name="date_end_filter"]').value;
    if (dateStart) params.set('date_start', dateStart);
    if (dateEnd) params.set('date_end', dateEnd);

    const sumFrom = document.querySelector('[name="sum_from_filter"]').value;
    const sumTo = document.querySelector('[name="sum_to_filter"]').value;
    if (sumFrom) params.set('sum_from', sumFrom);
    if (sumTo) params.set('sum_to', sumTo);

    // Сохраняем сортировку
    const urlParams = new URLSearchParams(window.location.search);
    const sort_by = urlParams.get('sort_by');
    const sort_order = urlParams.get('sort_order');
    if (sort_by) params.set('sort_by', sort_by);
    if (sort_order) params.set('sort_order', sort_order);

    params.set('page', '1');
    window.location.search = params.toString();
}