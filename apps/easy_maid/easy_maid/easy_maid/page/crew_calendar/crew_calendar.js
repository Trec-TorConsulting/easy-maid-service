frappe.pages['crew-calendar'].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: 'Crew Calendar',
    single_column: true,
  });

  const state = {
    status: '',
    employee: '',
  };

  page.add_field({
    label: __('Status'),
    fieldname: 'status',
    fieldtype: 'Select',
    options: '\nScheduled\nIn Progress\nCompleted\nCancelled',
    change() {
      state.status = this.get_value();
      loadCalendar();
    },
  });

  page.add_field({
    label: __('Employee'),
    fieldname: 'employee',
    fieldtype: 'Link',
    options: 'Employee',
    change() {
      state.employee = this.get_value();
      loadCalendar();
    },
  });

  const body = $('<div class="crew-calendar-content"></div>').appendTo(page.body);

  function loadCalendar() {
    body.html('<p>Loading visits...</p>');

    frappe.call({
      method: 'easy_maid.easy_maid.api.crew_calendar',
      args: {
        status: state.status || null,
        employee: state.employee || null,
      },
      callback: (r) => {
        const visits = r.message || [];

        if (!visits.length) {
          body.html('<p>No visits match the selected filters.</p>');
          return;
        }

        const grouped = {};
        for (const visit of visits) {
          const day = (visit.scheduled_start || '').slice(0, 10);
          grouped[day] = grouped[day] || [];
          grouped[day].push(visit);
        }

        const html = Object.keys(grouped)
          .sort()
          .map((day) => {
            const rows = grouped[day]
              .map(
                (v) => `
                  <li>
                    <strong>${frappe.datetime.str_to_user(v.scheduled_start)}</strong>
                    - ${frappe.utils.escape_html(v.customer || '')}
                    (${frappe.utils.escape_html(v.status || '')})
                  </li>`
              )
              .join('');

            return `
              <div class="mb-4">
                <h5>${frappe.datetime.str_to_user(day)}</h5>
                <ul>${rows}</ul>
              </div>
            `;
          })
          .join('');

        body.html(html);
      },
    });
  }

  loadCalendar();
};
