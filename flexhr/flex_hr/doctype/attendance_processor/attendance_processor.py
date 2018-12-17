# -*- coding: utf-8 -*-
# Copyright (c) 2018, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from flexhr.flex_hr.attendance_controller import run_job
from frappe.utils import parse_val

class AttendanceProcessor(Document):
	
	@frappe.whitelist()
	def call_run_job(self):
		run_job(self.from_date,self.to_date)
		return

@frappe.whitelist()
def precondition_for_auto_attendance():

	#Authorization code
	auth_token=frappe.db.get_single_value("Attendance Device Settings", "auth_token")
	if not auth_token:
		frappe.throw(_('Authorization code is missing in Attendance Device Settings'))

	#Holiday list for default company
	company=frappe.db.get_value("Global Defaults", None, "default_company")
	holiday_list = frappe.get_cached_value('Company',  company,  "default_holiday_list")
	if not holiday_list :
		frappe.throw(_('Please set a default Holiday List for Company {0}').format(company))

	
	#Employee with missing Attendance Device User ID 
	attendance_user_id=frappe.db.sql("""select employee_name from `tabEmployee`  
						where attendance_user_id is null
						and docstatus<2
						and status!='Left'""",as_list=1)
	if attendance_user_id:
		frappe.throw(_('Please set Attendance Device User ID for Employees {0}').format(parse_val(attendance_user_id)))
	
	# user_id should be present for sending emails

	#HR settings email template
	template = frappe.db.get_single_value('HR Settings', 'attendance_reconciliation_request_template')
	if not template:
		frappe.throw(_("Please set default template for Attendance Reconciliation Request in HR Settings."))
		
	template = frappe.db.get_single_value('HR Settings', 'attendance_reconciliation_information_template')
	if not template:
		frappe.throw(_("Please set default template for Attendance Reconciliation Information in HR Settings."))

	#Default shift with details
	shift_detail=frappe.db.sql("""select 
		working_hours,
		late_checkin_penalty_based_on,
		late_checkin_deduction_based_on,
		ignore_late_in,
		early_checkout_penalty_based_on,
		ignore_ealry_out,
		min_overtime_required,
		max_overtime_allowed
		from `tabShift Type` where is_default=1 and docstatus<2""",as_dict=1)
	if shift_detail:
		frappe.msgprint(_('Please check shift_detail {0}').format(shift_detail[0]))	

	return frappe.msgprint(_('All pre-check condition passed'))	

