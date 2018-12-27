frappe.ui.form.on('HR Settings', {
	onload: function(frm) {
		frm.fields_dict['default_leave_type_for_lwp'].get_query = function (doc) {
			return {
				query: "flexhr.api.default_leave_type_for_lwp"
			}
		}
	}
});
