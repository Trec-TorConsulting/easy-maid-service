frappe.pages['dispatch-board'].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: 'Dispatch Board',
    single_column: true,
  });

  const state = {
    date: frappe.datetime.get_today(),
  };

  page.add_date(__('Date'), state.date, (value) => {
    state.date = value;
    loadBoard();
  });

  const body = $('<div class="dispatch-board-content"></div>').appendTo(page.body);

  function loadBoard() {
    body.html('<p>Loading visits...</p>');

    frappe.call({
      method: 'easy_maid.easy_maid.api.dispatch_board',
      args: {
        start_date: state.date,
        end_date: state.date,
      },
      callback: (r) => {
        const visits = (r.message && r.message.visits) || [];

        if (!visits.length) {
          body.html('<p>No visits scheduled.</p>');
          return;
        }

        const rows = visits
          .map((v) => {
            const crew = (v.crew || []).map((c) => `${c.employee} (${c.role})`).join(', ') || 'Unassigned';
            const statusTag = v.unassigned
              ? '<span class="indicator red">Unassigned</span>'
              : `<span class="indicator blue">${v.status}</span>`;

            return `
              <tr>
                <td>${statusTag}</td>
                <td>${frappe.datetime.str_to_user(v.scheduled_start)}</td>
                <td>${frappe.utils.escape_html(v.customer || '')}</td>
                <td>${frappe.utils.escape_html(v.service_address || '')}</td>
                <td>${frappe.utils.escape_html(crew)}</td>
              </tr>
            `;
          })
          .join('');

        body.html(`
          <div class="table-responsive">
            <table class="table table-bordered table-hover">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Start</th>
                  <th>Customer</th>
                  <th>Address</th>
                  <th>Crew</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        `);
      },
    });
  }

  loadBoard();
};
