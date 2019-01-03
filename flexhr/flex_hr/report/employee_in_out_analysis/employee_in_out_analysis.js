
frappe.query_reports["Employee In Out Analysis"] = {
	"filters": [	
		{
			"fieldname":"from_date",
			"label": __("Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.month_start()
        },		
		{
			"fieldname":"to_date",
			"label": __("Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.month_end()
        },
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
            "options": "Company",
            "reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
        },
		{
			'fieldname': 'show_only_difference',
			'label': __("Show Only Difference"),
            'fieldtype': 'Select',
            "options" : ["Show Only Difference","Show All"],
            "reqd": 1,
            "default": "Show Only Difference"
        }

	]
}