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
from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words, getdate,time_diff_in_seconds,today

class EmployeeCheckin(Document):
	def after_insert(self):
		
		if self.status == 'Pass':
			print '@@@@@@@@@@@@@@@@@@@@'
		# 	attendance = frappe.db.get_list("Attendance",
		# 		{"employee": self.employee,
		# 		"attendance_date": datetime.datetime.now()},
		# 		["name"]
		# 	)
		# 	print '@@@@@@@@@@@@@@@@@@@@'
		# # 	if not attendance:
		# 		employee_doc = frappe.get_doc("Employee", self.employee)
		# 		## Create Employee Attendance
		# 		employee_attendance = frappe.new_doc("Attendance")
		# 		employee_attendance.company = employee_doc.company
		# 		employee_attendance.employee = employee_doc.name
		# 		employee_attendance.employee_name = employee_doc.employee_name
		# 		employee_attendance.status = "Present"
		# 		employee_attendance.attendance_date =  datetime.datetime.now()
		# 		employee_attendance.department = employee_doc.department
		# 		if self.att_type=='in' : employee_attendance.checkin_time = datetime.datetime(*time.strptime(str(self.att_time), "%Y-%m-%d %H:%M:%S")[:6])
		# 		if self.att_type=='out' : employee_attendance.checkin_time = datetime.datetime(*time.strptime(str(self.att_time), "%Y-%m-%d %H:%M:%S")[:6])
		# 		employee_attendance.save()
		# 		employee_attendance.submit()

		# if self.att_type=='out':
		# 	in_time = datetime.datetime(*time.strptime(str(self.att_time), "%Y-%m-%d %H:%M:%S")[:6])
		# 	out_time = datetime.datetime(*time.strptime(str(self.att_time), "%Y-%m-%d %H:%M:%S")[:6])
		# 	if in_time > out_time:
		# 		frappe.throw("Out-time must be later than In-time.")
		# 	else:
		# 		duration = out_time - in_time






	def validate(self):
		# if self.status=='Pass':
		# 	self.submit()
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
def create_attendance(emp,dt,emp_in_time,emp_out_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,status = "Present",review_status='Not Required',review_remark=None):
			attendance = frappe.db.sql("""select employee,attendance_date,name from `tabAttendance` where employee = %s\
				and attendance_date = %s and docstatus < 2""",(emp, dt), as_dict=1)
			if not attendance:
				employee_doc = frappe.get_doc("Employee", emp)
				## Create Employee Attendance
				employee_attendance = frappe.new_doc("Attendance")
				employee_attendance.company = employee_doc.company
				employee_attendance.employee = employee_doc.name
				employee_attendance.employee_name = employee_doc.employee_name
				employee_attendance.department = employee_doc.department
			# elif attendance:
			# 	attendance_name=attendance[0]['name']
			# 	## Update Employee Attendance
			# 	employee_attendance = frappe.get_doc("Attendance", attendance_name)
			# 	employee_attendance.docstatus=0
			# 	print 'inside update'
				employee_attendance.status = status
				employee_attendance.attendance_date = dt
				employee_attendance.checkin_time=emp_in_time
				employee_attendance.checkout_time=emp_out_time
				employee_attendance.duration=duration
				employee_attendance.shift_in_time=shift_start_time
				employee_attendance.shift_out_time=shift_end_time
				employee_attendance.shift_type=shift_type
				employee_attendance.delay=late_checkin_mins
				employee_attendance.early=early_checkout_mins
				employee_attendance.overtime=applicable_ot_mins
				employee_attendance.review_status=review_status
				employee_attendance.review_remark=review_remark
				employee_attendance.save()
				employee_attendance.submit()
				return employee_attendance.name






		








				
				
				
	







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











def get_employee_checkin_with_in_and_out(date):
	check_in=frappe.db.sql("""select 
		min(time(e1.att_time)) as in_time,
		min(e1.att_time) as in_date_time,
		max(time(e2.att_time)) as out_time,
		max(e2.att_time) as out_date_time,
		date(e1.att_date) as att_date,
		e1.employee as employee
		from `tabEmployee Checkin` e1
		inner join `tabEmployee Checkin` e2
		on e1.employee=e2.employee
		where e1.att_type='in'
		and e2.att_type='out'
		and date(e1.att_date)=%s
		group by e1.employee""",(date),as_dict=1)
	return check_in if check_in else None



def get_employee_checkin_with_out_only(date):
	pass


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




