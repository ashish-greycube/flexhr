# -*- coding: utf-8 -*-
# Copyright (c) 2018, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime, time
import frappe
from erpnext.hr.doctype.employee.employee import is_holiday
from erpnext.hr.doctype.leave_application.leave_application import get_leave_allocation_records
from frappe.model.document import Document
from werkzeug.wrappers import Response
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
	att_date_time=datetime.datetime.fromtimestamp(float(att_time)).strftime("%Y-%m-%d %H:%M:%S")
	att_date=att_date_time[:10]
	att_time=att_date_time[12:]
	check_in.att_date=att_date
	check_in.att_time = att_date_time
	check_in.status=status
	check_in.remark=remark
	check_in.save(ignore_permissions=True)
	if status=='Pass' or (status=='Fail' and remark == 'Employee Not Active. Left'):
		check_in.submit()
	print check_in.name
	

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

def get_late_checkin_penalty(shift_type,emp_in_time):
	shift_type = frappe.get_doc("Shift Type", shift_type)
	penalty_in_mins=0
	late_checkin_deduction_based_on=shift_type.get("late_checkin_deduction_based_on")
	if late_checkin_deduction_based_on =='Late Checkin Deduction Rules':
    		for condition in shift_type.get("late_checkin_deduction_rules"):
				if emp_in_time >= condition.from_time and emp_in_time <= condition.to_time:
					penalty_in_mins=condition.penalty
					return penalty_in_mins
	elif late_checkin_deduction_based_on =='Actual Minutes':
		shift_start_time=shift_type.get("start_time")
		ignore_late_in=shift_type.get("ignore_late_in")
		if emp_in_time>shift_start_time:
			allowed_late_in=shift_start_time+datetime.timedelta(minutes = ignore_late_in)
			if emp_in_time>allowed_late_in:
				penalty_in_mins=cint(time_diff_in_seconds(emp_in_time,shift_start_time)/60)
		return penalty_in_mins	
		
def get_early_checkout_penalty(shift_type,emp_out_time):
	penalty_in_mins=0
	shift_type = frappe.get_doc("Shift Type", shift_type)
	early_checkout_deduction_based_on=shift_type.get("early_checkout_deduction_based_on")
	if early_checkout_deduction_based_on =='Actual Minutes':
		shift_end_time=shift_type.get("end_time")
		print emp_out_time
		print shift_end_time
		if emp_out_time<shift_end_time:
			ignore_early_out=shift_type.get("ignore_early_out")
			allowed_early_out=shift_end_time-datetime.timedelta(minutes = ignore_early_out)
			if emp_out_time<allowed_early_out:
				penalty_in_mins=cint(time_diff_in_seconds(shift_end_time,emp_out_time)/60)
	return penalty_in_mins

def get_shift_detail_of_employee(employee, date):
	shift=frappe.db.sql("""select shift_type.name as shift_type from 
		`tabEmployee` as emp
		inner join `tabShift Assignment` as shift_assign
		on emp.employee = shift_assign.employee
		inner join `tabShift Type`as shift_type
		on shift_assign.shift_type = shift_type.name
		where emp.employee=%s
		and shift_assign.date=%s""",(employee, date), as_dict=1)

	if shift:
		shift_type=shift[0]["shift_type"]
		shift_type="'"+shift_type+"'"
		condition_str=' name ='+shift_type
	else:	
		condition_str=' is_default=1'
	
	shift=frappe.db.sql("""select name as shift_type ,start_time ,end_time,
	min_overtime_required,max_overtime_allowed,
	early_checkout_deduction_based_on,ignore_ealry_out,
	late_checkin_deduction_based_on
	from
	 `tabShift Type`
	where {condition_str}""".format(condition_str=condition_str),as_dict=1)
	return shift[0]


@frappe.whitelist(allow_guest=True)
def process_employee_checkin_records(start_date, end_date):
	checkin_days = date_diff(end_date,start_date) + 1
	for d in range(checkin_days):
		dt = add_days(cstr(getdate(start_date)), d)
		check_in=get_all_employee_checkin_detail(dt)
		if check_in:
			for emp in check_in:
				emp_id=emp['employee']
				print 'emp_id '+emp_id
				holiday=is_holiday(emp_id,dt)
				print 'holiday '+str(holiday)
				emp_att_date=emp['att_date']
				print 'dt '+dt
				print 'emp_att_date '+str(emp_att_date)
				att_detail=get_existing_attendance_detail(emp_id,dt)
				print 'att_detail '+str(att_detail)
				emp_name=emp['emp_name']
				leave_detail=get_leave_of_employee(emp_name,dt,status='Approved', docstatus=1)
				print 'leave_detail '+str(leave_detail)
				print '************'
				if leave_detail!=None:
					leave_name=leave_detail["leave_name"]

				if holiday==True and emp_att_date==None:
					print '1'
					remark='Holiday'
					action=''
					review=False
				elif holiday==True and emp_att_date!=None:
					print '2'
					remark='Holiday and Employee is present'
					action='Employee may avail Compensatory Leave Request'
					review=False
				elif holiday==False and emp_att_date==None and leave_detail!=None:
					print '3'
					remark='Working day and Employee has leave'+leave_name
					print remark
					action=''
					review=False
				elif holiday==False and emp_att_date==None and leave_detail==None:	
					print '4'
					remark='Working day and Employee is absent and No Leave Application '
					print remark
					description = 'Employee is absent on '+ dt +'as per attendace device record. Hence system has generated LWP'
					if att_detail==None:
						print '4.1'
						leave_name=create_lwp(emp_id,dt,description)
						action='Created LWP'+leave_name
						review=False
					elif att_detail!=None:
						print '4.2'
						remark='Discrepancy'
						action='?'
						review=True
				elif holiday==False and emp_att_date!=None:
					print '5'
					emp_in_time=emp['in_time']
					emp_out_time=emp['out_time']
					present_based_on=emp['present_based_on']
					if (emp_in_time==None and emp_out_time!=None ) or (emp_in_time!=None and present_based_on!='Checkin Data Only' and emp_out_time==None) :
					# above condition means absent
						print '5.1'
						if emp_in_time==None: emp_in_time='missing'
						if emp_out_time==None:emp_out_time='missing'

						if leave_detail!=None:
							print '5.1.1'
							remark='Employee, In '+str(emp_in_time)+' and Out is '+str(emp_out_time)+ ' and leave '+leave_name
							action='[A] Nothing to do as both in and out time not present OR [B] Cancel leave '+leave_name+' to give present'
							review=True
						elif leave_detail==None:
							#create lwp
							print '5.1.2'
							if att_detail==None:
								print '5.1.2.1'
								leave_name=create_lwp(emp_id,dt,description)
								remark = 'Employee, In '+str(emp_in_time)+' and Out is '+str(emp_out_time)+ '. Created LWP'+leave_name
								action='[A] Nothing to do as both in and out time not present OR [B] Cancel leave '+leave_name+' to give present'
								review=True
							elif att_detail!=None:
								print '5.1.2.2'
								remark='Discrepancy'
								action='?'
								review=True
					elif(emp_in_time!=None and emp_out_time!=None ) or (emp_in_time!=None and present_based_on=='Checkin Data Only' and emp_out_time==None):
					# above condition means present
						#get shift detail
						print '5.2'
						shift=get_shift_detail_of_employee(emp_id,dt)
						shift_type=shift['shift_type']
						shift_start_time=shift['start_time']
						shift_end_time=shift['end_time']

						emp_in_date_time=emp['in_date_time']
						emp_out_date_time=emp['out_date_time']
						duration=0
						status='Present'
						if emp_in_time and emp_out_time:
							duration = emp_out_time - emp_in_time
						#conditions
						ignore_late_checkin_deduction=emp['ignore_late_checkin_deduction']
						ignore_early_checkout_deduction=emp['ignore_early_checkout_deduction']

						#late checkin
						late_checkin_mins=0
						if ignore_late_checkin_deduction == 0:
							if emp_in_time>shift_start_time:
								late_checkin_mins = get_late_checkin_penalty(shift_type,emp_in_time)
						# early checkout
						early_checkout_mins=0
						applicable_ot_mins=0
						if emp_out_time:
							if ignore_early_checkout_deduction == 0:
								if emp_out_time<shift_end_time:
									early_checkout_mins=get_early_checkout_penalty(shift_type,emp_out_time)
							# overtime
							
							if emp_out_time>shift_end_time:
								is_eligible_for_attendace_based_overtime_earning=emp['is_eligible_for_attendace_based_overtime_earning']
								if is_eligible_for_attendace_based_overtime_earning==1:
									applicable_ot_mins=calculate_overtime(shift_type,emp_out_time)

						if leave_detail==None:
							if att_detail==None:
								att_name=create_attendance(emp_id,dt,emp_in_date_time,emp_out_date_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,status=status)
								remark='Attendance created '+att_name
								action=''
								review=False
							elif att_detail != None:
								if att_detail['checkin_time']==emp_in_time and  att_detail['checkout_time']==emp_out_time:
									remark='It is re-run'
									action=''
									review=False
								else:
									remark='Attendance record exist, and has different data then checkin'
									action='?'
									review=True
						elif leave_detail!=None:
							if late_checkin_mins==0 and early_checkout_mins==0 and applicable_ot_mins==0:
								#ask to cancel that day leave
								description='Present Date '+dt+' In '+str(emp_in_time)+ ' Out '+str(emp_out_time)+' Duration '+str(duration)
								update_leave_details(leave_name,description)
								remark='Employee is present for'+str(duration)+' and there is leave '+leave_name
								action='[A] Cancel leave'+leave_name+'for date '+dt+' OR [B]Ignore present, as it is approved leave'
								review=True								
							else:
								# create attendance request with details
								description='Present Date '+dt+' In '+str(emp_in_time)+ ' Out '+str(emp_out_time)+' Duration '+str(duration)
								update_leave_details(leave_name,description)
								explanation='Checkin Time'+str(emp_in_time)+ 'Checkout Time '+str(emp_out_time)+'Late Checkin (in Mins)'+str(late_checkin_mins)+'Early Checkout (in Mins)'+str(early_checkout_mins)+'Applicable OverTIme (in Mins)'+str(applicable_ot_mins)
								att_req=create_attendance_request(emp_id,dt,explanation)
								remark='Employee is present for '+str(duration)+' and there is leave '+leave_name +' and Late Checkin penalty '+str(late_checkin_mins)+' Early Checkout penalty '+str(early_checkout_mins)+' OT'+str(applicable_ot_mins)
								action='[A]Ignore attendance/penalty/OT OR [B] Cancel leave '+leave_name+' to give attendance'+' [B.1] Give penalty/OT'+att_req['name']
								review=True
				print '------------'
				print emp_id
				print remark
				print action
				print review
				print '------------'		

				
				
				
	
				
				# if emp_att_date == None:
				# #As per attendance device, employee is absent
				# 	if is_holiday(emp_id,dt)==False:
				# 		if leave_detail == None:
				# 			description = 'There is no Checkin Checkout data. Hence system has generated leave application'
				# 			create_lwp(emp_id,dt,description)
				# 			#no attendance entry required as LWP creates attendance record
				# 		else:
				# 		# do nothing as leave is present
				# 			pass
				# 	else:
				# 		# do nothing as it is holiday
				# 		pass
				# elif emp_att_date !=None:					
				# 	# as per attendance device he is present and there is no holiday
				# 	if is_holiday(emp_id,dt)==False:
				# 		emp_in_time=emp['in_time']
				# 		emp_out_time=emp['out_time']
				# 		print 'emp_in_time'
				# 		print emp_in_time
				# 		print 'emp_out_time'
				# 		print emp_out_time
				# 		print emp_name



				# 		if emp_in_time and emp_out_time:
				# 			duration = emp_out_time - emp_in_time
				# 			status='Present'
				# 		else:
				# 			#we have only checkin data
				# 			if emp_in_time!=None and emp_out_time==None:
				# 				print 'emp_in_time!=None and emp_out_time==None'
				# 				if present_based_on=='Checkin Data Only':
				# 					status='Present'
				# 				else:
				# 					status='Absent'
				# 					description = 'There is no Checkout data. Only Checkin data at '+ str(emp_in_time)
				# 					print description
				# 					print leave_detail
				# 					if leave_detail==None:
				# 						description =description+'. Hence system has generated leave application'
				# 						create_lwp(emp_id,dt,description)
				# 					else:
				# 						description=description+'. Hence take appropriate action.'
				# 						update_leave_details(leave_name,description)	
							
				# 			#we have checkout data only
				# 			if emp_in_time==None and emp_out_time!=None:
				# 				status='Absent'
				# 				description = 'There is no Checkin data. Only Checkout data at '+str(emp_out_time)
				# 				if leave_detail==None:
				# 					description =description+'. Hence system has generated leave application'
				# 					create_lwp(emp_id,dt,description)
				# 				else:
				# 					description=description+'. Hence take appropriate action.'
				# 					update_leave_details(leave_name,description)

				# 		# there is no leave and employee has checkin and out data
				# 		if leave_detail==None and status=='Present':
				# 			#late checkin
				# 			late_checkin_mins=0
				# 			if emp_in_time:
				# 				if ignore_late_checkin_deduction == 0:
				# 					if emp_in_time>shift_start_time:
				# 						late_checkin_mins = get_late_checkin_penalty(shift_type,emp_in_time)
							
				# 			# early checkout
				# 			early_checkout_mins=0
				# 			applicable_ot_mins=0

				# 			if emp_out_time:
				# 				if ignore_early_checkout_deduction == 0:
				# 					if emp_out_time<shift_end_time:
				# 						early_checkout_mins=get_early_checkout_penalty(shift_type,emp_out_time)
				# 						print 'early_checkout_mins	'
				# 						print early_checkout_mins
				# 				# overtime
				# 				if emp_out_time>shift_end_time:
				# 					is_eligible_for_attendace_based_overtime_earning=emp['is_eligible_for_attendace_based_overtime_earning']
				# 					if is_eligible_for_attendace_based_overtime_earning==1:
				# 						applicable_ot_mins=calculate_overtime(shift_type,emp_out_time)
				# 					print 'applicable_ot_mins'
				# 					print applicable_ot_mins
				# 			employee_attendance=create_attendance(emp_id,dt,emp_in_date_time,emp_out_date_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,status=status)
						
				# 		# there is leave and employee has checkin and out data
				# 		elif leave_detail!=None and status=='Present':
				# 			leave_application=frappe.get_doc("Leave Application", leave_name)
				# 			if leave_application:
				# 				leave_application.description='System cancelled leave as employee is present'
				# 				leave_application.cancel()
				# 				create_attendance(emp_id,dt,emp_in_date_time,emp_out_date_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,status=status,review_status=review_status,review_remark=review_remark)
				
				# 	else:
				# 	#it is holiday so no attendance record is created even if the device has checkin data
				# 		pass

def update_leave_details(leave_name,description):
	leave=frappe.get_doc("Leave Application",leave_name)
	leave.db_set('description', description+'  '+leave.description)
	# leave.save(ignore_permissions=True)

def create_attendance_request(emp_id,date,explanation,docstatus=0):
	att_req = frappe.db.sql("""select name from `tabAttendance Request`
where 
employee=%(emp_id)s and
and docstatus = %(docstatus)s
and (from_date between %(date)s and %(date)s
or to_date between %(date)s and %(date)s
or (from_date < %(date)s and to_date > %(date)s))
	""", {
		"date": date,
		"emp_id": emp_id,
		"docstatus": docstatus
	}, as_dict=1)
	if bool(att_req) == False:
		att_req=frappe.new_doc("Attendance Request")
		att_req.employee=emp_id
		att_req.from_date=date
		att_req.to_date=date
		att_req.reason='On Duty'
		att_req.explanation=explanation
		att_req.save(ignore_permissions=True)
		return att_req.name
	else:
		att_req[0]


def create_lwp(employee,date,description):
	leave = frappe.new_doc("Leave Application")
	leave.employee=employee
	leave.leave_type='Leave Without Pay'
	leave.from_date=date
	leave.to_date=date
	leave.description='Attendence System generated application'
	leave.status='Approved'
	leave.posting_date=today()
	leave.save(ignore_permissions=True)
	leave.submit()
	return leave.name

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


def get_existing_attendance_detail(emp_id,date):
	att_detail=frappe.db.sql("""select 
	name,status,leave_type,checkin_time,checkout_time 
	from `tabAttendance` where 
	employee=%s and
	attendance_date=%s and
	docstatus<2""",(emp_id,date),as_dict=1)
	return att_detail[0] if bool(att_detail) else None	

def get_leave_of_employee(employee_name,date, status='Approved', docstatus=1):
	leave_detail = frappe.db.sql("""select name as leave_name,leave_type
		from `tabLeave Application`
        where employee_name=%(employee_name)s 
			and status = %(status)s 
            and docstatus = %(docstatus)s
            and half_day=0 
			and (from_date between %(date)s and %(date)s
				or to_date between %(date)s and %(date)s
				or (from_date < %(date)s and to_date > %(date)s))
	""", {
		"date": date,
		"employee_name": employee_name,
		"status": status,
		"docstatus": docstatus
	}, as_dict=1)
	return leave_detail[0] if bool(leave_detail) else None

def calculate_overtime(shift_type,emp_out_time):
	shift_type = frappe.get_doc("Shift Type", shift_type)
	shift_end_time=shift_type.get("end_time")
	min_overtime_required=shift_type.get("min_overtime_required")
	max_overtime_allowed=shift_type.get("max_overtime_allowed")
	applicable_ot_mins=0
	# ot_amount=0

	if emp_out_time>shift_end_time:
		overtime=cint(time_diff_in_seconds(emp_out_time,shift_end_time)/60)
		if overtime>=min_overtime_required and overtime<=max_overtime_allowed:
			applicable_ot_mins=overtime
		elif overtime>max_overtime_allowed:
			applicable_ot_mins=max_overtime_allowed
		else:
			applicable_ot_mins=0
		# ot_factor = frappe.db.get_value("Company", company, "overtime_earning_factor")
		# ot_amount=applicable_ot_mins*ot_factor
	return applicable_ot_mins





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

def get_all_employee_checkin_detail(date):
	check_in=frappe.db.sql("""
select min(in_time) in_time,min(in_date_time) in_date_time , max(out_time) out_time, max(out_date_time) out_date_time,att_date,
emp.employee, emp.employee_name as emp_name,emp.salary_slip_based_on,emp.present_based_on,
emp.is_eligible_for_attendace_based_overtime_earning,emp.ignore_late_checkin_deduction,emp.ignore_early_checkout_deduction
from
`tabEmployee` emp
left outer join 
(
	select date(att_date) as att_date, employee, min(time(att_time)) as in_time,min(date(att_time)) as in_date_time, null out_time , null out_date_time
	from `tabEmployee Checkin`
	where att_type='in' and att_date = %s and status = 'Pass'
	group by att_date, employee
	union all
	select date(att_date) as att_date, employee, null in_time,null in_date_time, max(time(att_time)) out_time,max(date(att_time)) as out_date_time
	from `tabEmployee Checkin`
	where att_type='out' and att_date = %s and status = 'Pass'
	group by att_date, employee
) t on t.employee=emp.name
where 
ifnull(emp.relieving_date, '2199-12-31') >= %s and
emp.salary_slip_based_on='Attendance'
group by att_date, employee""",(date,date,date),as_dict=1)
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

