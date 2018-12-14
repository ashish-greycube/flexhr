// Copyright (c) 2016, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Attendance Reconciliation"] = {
	"filters": [	
		{
			"fieldname":"from_date",
			"label": __("Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},		
		{
		"fieldname":"employee",
		"label": __("Employee"),
		"fieldtype": "Link",
		"options": "Employee"
		}

	]
}
