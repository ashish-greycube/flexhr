# -*- coding: utf-8 -*-
# Copyright (c) 2018, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime, time
import frappe
from frappe.model.document import Document
from werkzeug.wrappers import Response
from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words, getdate,time_diff_in_seconds

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
	print frappe.session.user
	print '00000000000'
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
	att_date_time=datetime.datetime.fromtimestamp(float(att_time)).strftime("%Y-%m-%d %H:%M:%S")
	att_date=att_date_time[:10]
	att_time=att_date_time[12:]
	check_in.att_date=att_date
	check_in.att_time = att_date_time
	check_in.status=status
	check_in.remark=remark
	check_in.insert(ignore_permissions=True)
	print check_in.name
	

@frappe.whitelist(allow_guest=True)
def create_attendance_record(from_date,to_date):

		check_in_entries = frappe.db.sql("""
			select 
				"Journal Entry" as payment_document, t1.name as payment_entry, 
				t1.cheque_no as cheque_number, t1.cheque_date, 
				t2.debit_in_account_currency as debit, t2.credit_in_account_currency as credit, 
				t1.posting_date, t2.against_account, t1.clearance_date, t2.account_currency 
			from
				`tabJournal Entry` t1, `tabJournal Entry Account` t2
			where
				t2.parent = t1.name and t2.account = %s and t1.docstatus=1
				and t1.posting_date >= %s and t1.posting_date <= %s 
				and ifnull(t1.is_opening, 'No') = 'No' {0}
			order by t1.posting_date ASC, t1.name DESC
		""".format(condition), (self.bank_account, self.from_date, self.to_date), as_dict=1)






@frappe.whitelist(allow_guest=True)
def get_shift_detail_of_employee(employee, date):
	shift=frappe.db.sql("""select shift_type.name as shift_type ,shift_type.start_time as start_time,shift_type.end_time as end_time from 
		`tabEmployee` as emp
		inner join `tabShift Assignment` as shift_assign
		on emp.employee = shift_assign.employee
		inner join `tabShift Type`as shift_type
		on shift_assign.shift_type = shift_type.name
		where emp.employee=%s
		and shift_assign.date=%s""",(employee, date), as_dict=1)
	return shift if shift else get_default_shift()

@frappe.whitelist(allow_guest=True)
def get_delay_penalty(shift_type,emp_in_time):
	shift_type = frappe.get_doc("Shift Type", "Regular Shift")
	delay_checkin_penalty_based_on=shift_type.get("delay_checkin_penalty_based_on")
	if delay_checkin_penalty_based_on =='Delay Penalty Rules':
    		for condition in shift_type.get("delay_penalty_rules"):
				if emp_in_time >= condition.from_time and emp_in_time <= condition.to_time:
					print 'p'
					print condition.penalty
					return condition.penalty

def get_default_shift():
	shift=frappe.db.sql("""select name as shift_type ,start_time ,end_time,
	min_overtime_required,max_overtime_allowed,
	early_checkout_penalty_based_on,ignore_ealry_out,
	delay_checkin_penalty_based_on
	from
	 `tabShift Type`
	where is_default=1""", as_dict=1)
	return shift[0]

@frappe.whitelist(allow_guest=True)
def get_employee_checkin_time(employee,date):
	check_in=frappe.db.sql("""select min(time(att_time)) as in_time,date(att_time) as att_date
		from `tabEmployee Checkin`
		where employee =%s 
		and date(att_time)=%s
		and att_type='in'""",(employee,date),as_dict=1)
	return check_in[0] if check_in else None


def get_employee_checkout_time(employee,date):
	check_out=frappe.db.sql("""select max(time(att_time)) as out_time
		from `tabEmployee Checkin`
		where employee =%s 
		and date(att_time)=%s
		and att_type='out'""",(employee,date),as_dict=1)
	return check_out[0] if check_out else None

@frappe.whitelist(allow_guest=True)
def process_employee_checkin_records(start_date, end_date, company=None):
	if company==None:company=frappe.db.get_single_value('Global Defaults', 'default_company')
	checkin_days = date_diff(end_date,start_date) + 1
	for d in range(checkin_days):
		dt = add_days(cstr(getdate(start_date)), d)
		check_in=get_employee_checkin_with_in_and_out(dt)
		for emp in check_in:
			print emp['employee']
			shift=get_shift_detail_of_employee(emp['employee'],dt)
			print shift

			shift_start_time=shift['start_time']
			emp_in_time=emp['in_time']
			
			#late entry
			print 'late'
			print emp_in_time
			if emp_in_time>shift_start_time:
				get_delay_penalty(shift['shift_type'],emp_in_time)

			shift_end_time=shift['end_time']
			emp_out_time=emp['out_time']
			print emp_out_time
			print shift_end_time
			# early leaving
			if emp_out_time<shift_end_time:
				early_checkout_penalty_based_on=shift['early_checkout_penalty_based_on']
				ignore_ealry_out=shift['ignore_ealry_out']
				early_in_mins=calculate_early_checkout_penalty(shift_end_time,emp_out_time,early_checkout_penalty_based_on,ignore_ealry_out)
				print early_in_mins
			# overtime
			if emp_out_time>shift_end_time:
				min_overtime_required=shift['min_overtime_required'] 
				max_overtime_allowed=shift['max_overtime_allowed']
				applicable_ot,ot_amount=calculate_overtime(shift_end_time,emp_out_time,min_overtime_required,max_overtime_allowed,company)
				print applicable_ot,ot_amount




def calculate_early_checkout_penalty(shift_end_time,emp_out_time,early_checkout_penalty_based_on,ignore_ealry_out):
	early=0
	if emp_out_time<shift_end_time:
		allowed_early_out=shift_end_time-datetime.timedelta(minutes = ignore_ealry_out)
		if emp_out_time<allowed_early_out:
			early=cint(time_diff_in_seconds(shift_end_time,emp_out_time)/60)
			
	return early if early else 0

def calculate_overtime(shift_end_time,emp_out_time,min_overtime_required,max_overtime_allowed,company):
	applicable_ot=0
	ot_amount=0

	if emp_out_time>shift_end_time:
		overtime=cint(time_diff_in_seconds(emp_out_time,shift_end_time)/60)
		if overtime>=min_overtime_required and overtime<=max_overtime_allowed:
			applicable_ot=overtime
		elif overtime>max_overtime_allowed:
			applicable_ot=max_overtime_allowed
		else:
			applicable_ot=0
		ot_factor = frappe.db.get_value("Company", company, "overtime_multiplication_factor")
		ot_amount=applicable_ot*ot_factor
	return applicable_ot,ot_amount


def get_all_absent_employee(date):
	# absent=("""select employee 
	# 	from `tabEmployee`
	# 	where employee not in
	# 	(select employee from
	# 	`tabEmployee Checkin` 
	# 	where date(att_date)=%s
	# 	and status='Pass')
	# 	and status='Active'""",(date),as_dict=1)
	# return absent if absent else None
	pass


def get_employee_checkin_with_in_and_out(date):
	check_in=frappe.db.sql("""select 
		min(time(e1.att_time)) as in_time,
		max(time(e2.att_time)) as out_time,
		date(e1.att_date) as att_date,
		e1.employee as employee
		from `tabEmployee Checkin` e1
		inner join `tabEmployee Checkin` e2
		on e1.employee=e2.employee
		where e1.att_type='in'
		and e2.att_type='out'
		and date(e1.att_date)=%s
		group by e1.employee""",(date),as_dict=1)
	return check_in

def get_employee_checkin_with_in_only(date):
	pass

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

