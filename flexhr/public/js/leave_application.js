frappe.ui.form.on("Leave Application", {
	half_day_date(frm) {
		frm.trigger("check_is_holiday");
    },
    check_is_holiday: function(frm) {
		if(frm.doc.from_date && frm.doc.to_date && frm.doc.employee && frm.doc.leave_type && frm.doc.half_day_date) {
        // server call is done to include holidays in leave days calculations
            console.log('check_is_holiday')
			return frappe.call({
                
				method: 'flexhr.api.is_holiday_on_half_date',
				args: {
					"employee": frm.doc.employee,
					"leave_type": frm.doc.leave_type,
					"half_day_date": frm.doc.half_day_date,
				},
				callback: function(r) {
					if (r && r.message) {
                        console.log(r)
                        if (r.message==true){
                            frappe.msgprint(__("Half day date cann't be on holiday"));
                            frm.set_value('half_day_date', '');

                        }
						
					}
				}
			});
		}
	},
});