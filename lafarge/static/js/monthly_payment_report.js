(() => {
    const table = document.getElementById('monthly-payment-table');
    if (!table) return;

    const tbody = table.tBodies[0];
    const headers = Array.from(table.tHead.rows[0].cells);
    const rows = Array.from(tbody.rows);
    const collator = new Intl.Collator(document.documentElement.lang || 'en', {
        numeric: true,
        sensitivity: 'base',
    });

    const valueFor = (row, column) => {
        const cell = row.cells[column];
        return (cell.dataset.sortValue ?? cell.textContent).trim();
    };

    headers.forEach((header, column) => {
        const button = header.querySelector('.payment-sort-button');

        button.addEventListener('click', () => {
            const ascending = header.getAttribute('aria-sort') !== 'ascending';
            const direction = ascending ? 1 : -1;
            // Start from the original order so equal values remain stable.
            const sortedRows = rows.slice().sort((left, right) => {
                const a = valueFor(left, column);
                const b = valueFor(right, column);

                // Missing dates, methods, details and subtotals stay at the end.
                if (!a || !b) return a === b ? 0 : (a ? -1 : 1);

                let result;
                if (header.dataset.sortType === 'number') {
                    result = Number(a) - Number(b);
                } else if (header.dataset.sortType === 'date') {
                    // ISO dates compare chronologically, without locale parsing.
                    result = a < b ? -1 : (a > b ? 1 : 0);
                } else {
                    result = collator.compare(a, b);
                }
                return result * direction;
            });

            const fragment = document.createDocumentFragment();
            sortedRows.forEach((row, index) => {
                // Sorting may separate invoices with the same payment details.
                // Keep subtotal cells with their invoice, but remove group borders
                // that would now imply unrelated adjacent rows belong together.
                row.classList.remove(
                    'border-top', 'border-bottom', 'border-start', 'border-end',
                    'border-secondary', 'table-row-light', 'table-row-dark',
                );
                row.classList.add(index % 2 === 0 ? 'table-row-light' : 'table-row-dark');
                fragment.appendChild(row);
            });
            tbody.appendChild(fragment);

            headers.forEach((otherHeader) => {
                const active = otherHeader === header;
                otherHeader.setAttribute('aria-sort', active ? (ascending ? 'ascending' : 'descending') : 'none');
                otherHeader.querySelector('.sort-indicator').textContent = active ? (ascending ? '↑' : '↓') : '↕';
            });
        });
    });
})();
