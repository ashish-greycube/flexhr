# -*- coding: utf-8 -*-
# Copyright (c) 2018, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class EmployeeCheckinUploader(Document):
	def validate(self):
		if not self.in_time and not self.out_time:
			frappe.throw(_("Either in or out time should be present. It is missing for {0} ").format(self.attendance_user_id))
		# emp_id=self.validate_attendance_user_id()
		# if not emp_id:
		# 	frappe.throw(_("Attendance ID {0} doesn't match any employee").format(self.attendance_user_id))

		employee = frappe.get_value('Employee', {'attendance_user_id': self.attendance_user_id}, "name")
		if employee:
			employee_doc = frappe.get_doc("Employee", employee)
			if employee_doc.status == 'Left':
				remark = 'Employee Not Active. Left'
				frappe.throw(_("Attendance ID {0} match {1} employee who has left organization").format(self.attendance_user_id,employee_doc.employee_name))
			else:
				status = 'Pass'
				remark = 'Inserted by Data Import'
				auth_token=frappe.db.get_single_value("Attendance Device Settings", "auth_token")
				stgid=None
				if (self.out_time and self.in_time) and(self.out_time <= self.in_time):
					frappe.throw(_("Out Time Should Be Greater Than In Time"))	


				if self.in_time and self.attendance_user_id and self.att_date:
					att_type='in'
					att_time=self.in_time
					create_checkin_record(att_type,stgid,self.att_date,att_time,self.attendance_user_id,auth_token,employee,remark,status)

				if self.out_time and self.attendance_user_id and self.att_date:
					att_type='out'
					att_time=self.out_time
					create_checkin_record(att_type,stgid,self.att_date,att_time,self.attendance_user_id,auth_token,employee,remark,status)
		else:
			frappe.throw(_("Attendance ID {0} doesn't match any employee").format(self.attendance_user_id))


def create_checkin_record(att_type,stgid,att_date,att_time,userid,auth_token,employee,remark,status):
	check_in = frappe.new_doc("Employee Checkin")
	check_in.employee = employee
	check_in.attendance_user_id = userid
	check_in.device_id=stgid
	check_in.auth_token=auth_token
	check_in.att_type = att_type
	check_in.att_date=att_date
	check_in.att_time = att_time
	check_in.status=status
	check_in.remark=remark
	check_in.save(ignore_permissions=True)
	if status=='Pass' or (status=='Fail' and remark == 'Employee Not Active. Left'):
		check_in.submit()

	# def validate_attendance_user_id(self):
	# 	emp_id = frappe.db.sql("""select 
	# name as emp_id 
	# from `tabEmployee` where attendance_user_id=%s""",self.attendance_user_id)[0][0]
	# 	return emp_id if emp_id else None
