from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Attendance"),
			"items": [
                {
					"type": "doctype",
					"name": "Leave Application",
				},
                				{
					"type": "doctype",
					"name": "Attendance",
                    "label": _("Attendance")
				},
				{
					"type": "doctype",
					"name": "Attendance Request",
				}
			]
		},
		{
			"label": _("Device Data"),
			"items": [

				{
					"type": "doctype",
					"name": "Employee Checkin",
				}
			]
		},
		{
			"label": _("Payroll"),
			"items": [
                {
					"type": "doctype",
					"name": "Additional Salary Entry",
				},
				{
					"type": "doctype",
					"name": "Payroll Entry"
				}
			]
		},
        		{
			"label": _("Nightly Job"),
			"items": [
				{
					"type": "doctype",
					"name": "Attendance Log",
				},
				{
					"type": "doctype",
					"name": "Attendance Processor",
				}
			]
		},
        		{
			"label": _("Attendance Setup"),
			"items": [
								{
					"type": "doctype",
					"name": "Attendance Device Settings",
				},
                {
					"type": "doctype",
					"name": "Shift Type",
				},
                {
					"type": "doctype",
					"name": "Employee",
				},
                                {
					"type": "doctype",
					"name": "HR Settings",
				},

                {
					"type": "doctype",
					"name": "Holiday List",
				}
			]
		},
		{
			"label": _("Additional Salary Setup"),
			"items": [
                {
					"type": "doctype",
					"name": "Company",
				},
                {
					"type": "doctype",
					"name": "Salary Component",
				}
			]
		},

		{
			"label": _("Overtime"),
			"items": [
				{
					"type": "doctype",
					"name": "Overtime Application",
                    "hide_count": False
				}
			]
		},

		{
			"label": _("Device Down"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee Checkin Uploader",
				}
			]
		}
	
	]