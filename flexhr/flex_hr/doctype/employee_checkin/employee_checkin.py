# -*- coding: utf-8 -*-
# Copyright (c) 2018, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime, time
import frappe
from frappe import _
from erpnext.hr.doctype.employee.employee import is_holiday
from erpnext.hr.doctype.leave_application.leave_application import get_leave_allocation_records
from frappe.model.document import Document
from werkzeug.wrappers import Response
from frappe.utils import get_url_to_form,formatdate
from frappe.utils import nowdate
from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words, getdate,time_diff_in_seconds,today

class EmployeeCheckin(Document):
	def validate(self):
		if getdate(self.att_date) > getdate(nowdate()):
			frappe.throw(_("Attendance can not be marked for future dates"))


#Extra functions
def is_leave_updated(att_name,review_remark):
	att_review_remark=frappe.get_value("Attendance",att_name, 'review_remark')
	if review_remark==att_review_remark:
		return True
	else:
		return False


def create_overtime_application(employee,date,ot_mins,employee_attendance):
	ota = frappe.new_doc("Overtime Application")
	ota.employee_name=employee
	ota.ot_date=date
	ota.applicable_ot_mins=ot_mins
	ota.approved_ot_mins=ot_mins
	ota.description='System generated application. Please approve or reject before payroll cycle'
	ota.status='Open'
	ota.attendance=employee_attendance
	ota.save()