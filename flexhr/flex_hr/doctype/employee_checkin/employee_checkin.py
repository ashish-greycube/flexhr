# -*- coding: utf-8 -*-
# Copyright (c) 2018, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime, time
import frappe
from frappe.model.document import Document
from werkzeug.wrappers import Response

class EmployeeCheckin(Document):
	def validate(self):
		pass
		# if self.employee:
		# 	attendance = frappe.db.get_list("Attendance",
		# 		{"employee": self.employee,
		# 		"attendance_date": datetime.datetime.now()},
		# 		["name"]
		# 	)
		# 	if not attendance:
		# 		employee_doc = frappe.get_doc("Employee", self.employee)
		# 		## Create Employee Attendance
		# 		employee_attendance = frappe.new_doc("Attendance")
		# 		employee_attendance.company = employee_doc.company
		# 		employee_attendance.employee = employee_doc.name
		# 		employee_attendance.employee_name = employee_doc.employee_name
		# 		employee_attendance.status = "Present"
		# 		employee_attendance.attendance_date =  datetime.datetime.now()
		# 		employee_attendance.department = employee_doc.department
		# 		employee_attendance.save()
		# 		employee_attendance.submit()

		# if self.out_time:
		# 	in_time = datetime.datetime(*time.strptime(str(self.in_time), "%Y-%m-%d %H:%M:%S")[:6])
		# 	out_time = datetime.datetime(*time.strptime(str(self.out_time), "%Y-%m-%d %H:%M:%S")[:6])
		# 	if in_time > out_time:
		# 		frappe.throw("Out-time must be later than In-time.")
		# 	else:
		# 		duration = out_time - in_time
		# 		self.duration = duration


@frappe.whitelist(allow_guest=True)
def punch_in(att_type,stgid,att_time,userid,auth_token=None):
	employee = frappe.get_value('Employee', {'attendance_user_id': userid}, "name")
	if auth_token:
		if auth_token != frappe.db.get_single_value("Attendance Device Settings", "auth_token"):
			remark = "Authorization Token Doesn't Match"
			status = 'Fail'
			create_checkin_record(att_type,stgid,att_time,userid,auth_token,employee,remark,status)
			return standard_response()
		else:
			if employee:
				employee_doc = frappe.get_doc("Employee", employee)
				if employee_doc.status == 'Left':
					remark = 'Employee Not Active. Left'
					status = 'Fail'
					create_checkin_record(att_type,stgid,att_time,userid,auth_token,employee,remark,status)
					return standard_response()
				else:
					remark = ''
					status = 'Pass'
					create_checkin_record(att_type,stgid,att_time,userid,auth_token,employee,remark,status)
					return standard_response()
			else:
				remark = "Attendance Userid Doesn't Match With Any Employee"
				status = 'Fail'
				employee=None
				create_checkin_record(att_type,stgid,att_time,userid,auth_token,employee,remark,status)
				return standard_response()
	else:
		remark = 'Authorization Token Not Found'
		status = 'Fail'
		auth_token=None
		create_checkin_record(att_type,stgid,att_time,userid,auth_token,employee,remark,status)
		return standard_response()

def standard_response():
	response = Response()
	response.mimetype = 'text/plain'
	response.charset = 'utf-8'
	response.data = 'OK'
	return response


@frappe.whitelist(allow_guest=True)
def create_checkin_record(att_type,stgid,att_time,userid,auth_token,employee,remark,status):
	check_in = frappe.new_doc("Employee Checkin")
	check_in.employee = employee
	check_in.attendance_user_id = userid
	check_in.device_id=stgid
	check_in.auth_token=auth_token
	check_in.att_type = att_type
	check_in.att_time = datetime.datetime.fromtimestamp(float(att_time)).strftime("%Y-%m-%d %H:%M:%S")
	check_in.status=status
	check_in.remark=remark
	check_in.insert(ignore_permissions=True)
	print check_in.name
	print '-------------------------------------'

@frappe.whitelist(allow_guest=True)
def punch_out(att_type,stgid,att_time,userid,auth_token=None):
	check_in = frappe.new_doc("Attendance Device Log")
	check_in.attendance_user_id = userid
	check_in.device_id=stgid
	check_in.auth_token=auth_token
	check_in.att_type = att_type
	check_in.save(ignore_permissions=True)
	print check_in.name
	print '-----------------------------------'

