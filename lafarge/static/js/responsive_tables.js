/* Enhance the existing tables in place: preserve rows, links, forms and sort handlers. */
(() => {
  const portrait = window.matchMedia(
    "(max-width: 700px) and (orientation: portrait)",
  );
  const tables = document.querySelectorAll(
    ".erp-app main table, #result_list, .inline-group table",
  );
  let sequence = 0;

  tables.forEach((table) => {
    if (table.dataset.responsiveReady || !table.tHead) return;
    table.dataset.responsiveReady = "true";
    const nested = Boolean(table.parentElement.closest("table"));
    const headers = Array.from(table.tHead.rows[0].cells);
    const rows = Array.from(table.tBodies).flatMap((body) =>
      Array.from(body.rows),
    );
    const headerControls = Array.from(
      table.tHead.querySelectorAll("a, button"),
    ).map((control) => ({
      control,
      tabindex: control.getAttribute("tabindex"),
    }));
    const labelFor = (header) => header.textContent.replace(/\s+/g, " ").trim();
    const labels = headers.map(labelFor);
    const stackable =
      Boolean(table.closest(".erp-app")) &&
      table.tHead.rows.length === 1 &&
      !table.querySelector('[rowspan]:not([rowspan="1"])');
    const keyColumn = Math.max(
      0,
      labels.findIndex((label) =>
        /^(invoice(?: number| no\.)?|number|product(?: name)?|customer(?: name)?|name|period|month)$/i.test(
          label,
        ),
      ),
    );
    const viewport = document.createElement("div");
    viewport.className = "responsive-table-viewport";
    viewport.id = `table-viewport-${++sequence}`;
    viewport.tabIndex = 0;
    viewport.setAttribute("role", "region");
    viewport.setAttribute(
      "aria-label",
      table.closest("[aria-label]")?.getAttribute("aria-label") || "Data table",
    );
    table.before(viewport);
    viewport.append(table);
    table.classList.add("responsive-data-table");
    table.closest(".table-responsive")?.classList.add("responsive-table-host");

    // Keep native table roles when the portrait CSS lays rows out as record cards.
    if (stackable) {
      table.classList.add("record-table");
      table.setAttribute("role", "table");
      table.tHead.setAttribute("role", "rowgroup");
      table.tHead.rows[0].setAttribute("role", "row");
      headers.forEach((header) => header.setAttribute("role", "columnheader"));
      Array.from(table.tBodies).forEach((body) =>
        body.setAttribute("role", "rowgroup"),
      );
      rows.forEach((row) => {
        row.setAttribute("role", "row");
        const cells = Array.from(row.cells);
        const full = cells.length === 1 && cells[0].colSpan > 1;
        const summary = !full && cells.some((cell) => cell.colSpan > 1);
        row.classList.add(
          full
            ? "record-full-row"
            : summary
              ? "record-summary-row"
              : "record-data-row",
        );
        cells.forEach((cell, index) => {
          cell.setAttribute("role", "cell");
          if (full || summary) return;
          cell.dataset.label = labels[index] || "Actions";
          if (index === keyColumn) cell.classList.add("record-key-cell");
          if (
            /customer|product|items|address|details|office hour/i.test(
              labels[index],
            )
          )
            cell.classList.add("record-wide-cell");
          if (cell.querySelector("table"))
            cell.classList.add("record-nested-cell");
          if (
            !labels[index] &&
            !cell.textContent.trim() &&
            !cell.querySelector("a, button, input")
          )
            cell.classList.add("record-spacer");
        });
      });
    }

    // Pin identifiers in flat data tables. Editors need their full width for fields.
    if (
      !table.querySelector("tbody table") &&
      !table.closest(".inline-group")
    ) {
      headers[keyColumn]?.classList.add("erp-sticky-key");
      rows.forEach((row) => {
        if (row.cells.length === headers.length)
          row.cells[keyColumn]?.classList.add("erp-sticky-key");
      });
    }
    if (stackable && !nested) {
      const controls = document.createElement("div");
      controls.className = "record-table-controls";
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "record-view-toggle";
      toggle.textContent = "Table view";
      toggle.setAttribute("aria-controls", viewport.id);
      toggle.setAttribute("aria-pressed", "false");
      toggle.addEventListener("click", () => {
        const tabular = viewport.classList.toggle("show-table");
        viewport
          .querySelectorAll(".responsive-table-viewport")
          .forEach((child) => child.classList.toggle("show-table", tabular));
        toggle.setAttribute("aria-pressed", String(tabular));
        toggle.textContent = tabular ? "Record view" : "Table view";
        updateOverflow();
      });
      controls.append(toggle);

      // Proxy existing controls instead of implementing a second sorting algorithm.
      const sorters = headers
        .map((header, index) => ({
          header,
          label: labels[index],
          source: header.querySelector("a, button"),
        }))
        .filter((item) => item.source);
      if (sorters.length) {
        const details = document.createElement("details");
        details.className = "record-sort-menu";
        const summary = document.createElement("summary");
        summary.textContent = "Sort records";
        const choices = document.createElement("div");
        choices.className = "record-sort-options";
        sorters.forEach(({ header, label, source }) => {
          const button = document.createElement("button");
          button.type = "button";
          const refresh = () => {
            const direction =
              header.getAttribute("aria-sort") ||
              (header.classList.contains("ascend")
                ? "ascending"
                : header.classList.contains("descend")
                  ? "descending"
                  : "none");
            button.textContent =
              label +
              (direction === "ascending"
                ? " ↑"
                : direction === "descending"
                  ? " ↓"
                  : "");
            button.setAttribute(
              "aria-label",
              `Sort by ${label}${direction === "none" ? "" : `, currently ${direction}`}`,
            );
          };
          refresh();
          button.addEventListener("click", () => source.click());
          new MutationObserver(refresh).observe(header, {
            attributes: true,
            attributeFilter: ["aria-sort", "class"],
          });
          choices.append(button);
        });
        details.append(summary, choices);
        controls.append(details);
      }
      viewport.before(controls);
    }

    function updateOverflow() {
      const overflow = viewport.scrollWidth > viewport.clientWidth + 2;
      const cards =
        stackable &&
        portrait.matches &&
        !viewport.classList.contains("show-table");
      viewport.classList.toggle("is-overflowing", overflow);
      viewport.tabIndex = overflow ? 0 : -1;
      headerControls.forEach(({ control, tabindex }) => {
        if (cards) control.tabIndex = -1;
        else if (tabindex === null) control.removeAttribute("tabindex");
        else control.setAttribute("tabindex", tabindex);
      });
      if (cards) viewport.scrollLeft = 0;
    }
    new ResizeObserver(updateOverflow).observe(viewport);
    new ResizeObserver(updateOverflow).observe(table);
    portrait.addEventListener("change", updateOverflow);
    updateOverflow();
  });
})();
