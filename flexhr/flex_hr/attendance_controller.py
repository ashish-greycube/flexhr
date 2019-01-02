from __future__ import unicode_literals
import frappe
from frappe import _
from werkzeug.wrappers import Response
import datetime
from erpnext.hr.doctype.employee.employee import is_holiday
from erpnext.hr.doctype.leave_application.leave_application import get_number_of_leave_days,get_leave_approver
from frappe.utils import get_url_to_form,formatdate,split_emails
from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words,time_diff_in_seconds,today,now_datetime

# Attendance device related functions
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
	check_in.att_time = att_time
	check_in.status=status
	check_in.remark=remark
	check_in.save(ignore_permissions=True)
	if status=='Pass' or (status=='Fail' and remark == 'Employee Not Active. Left'):
		check_in.submit()
	print check_in.name


#Nightly run related functions

# insert data related functions
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
				employee_attendance.status = status
				employee_attendance.attendance_date = dt
				if emp_in_time==None:
					employee_attendance.checkin_time=""
				else:
					employee_attendance.checkin_time=emp_in_time
				if emp_out_time==None:
					employee_attendance.checkout_time=""
				else:
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

def create_lwp(employee,date,description,follow_via_email=0):
	leave_type = frappe.db.get_single_value('HR Settings', 'default_leave_type_for_lwp')
	leave = frappe.new_doc("Leave Application")
	leave.employee=employee
	leave.leave_type=leave_type
	leave.from_date=date
	leave.to_date=date
	leave.description=description
	leave.status='Approved'
	leave.posting_date=today()
	leave.follow_via_email=follow_via_email
	leave.save(ignore_permissions=True)
	leave.submit()
	return leave.name
		


def create_attendance_request(emp_id,date,emp_in_time,emp_out_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,explanation):
		att_req=frappe.new_doc("Attendance Request")
		att_req.employee=emp_id
		att_req.from_date=date
		att_req.to_date=date
		att_req.reason='On Duty'
		att_req.explanation=explanation
		if emp_in_time==None:
			att_req.checkin_time=""
		else:
			att_req.checkin_time=emp_in_time
		if emp_out_time==None:
			att_req.checkout_time=""
		else:
			att_req.checkout_time=emp_out_time
		if duration==None:
			att_req.duration=""
		else:
			att_req.duration=duration
		att_req.shift_in_time=shift_start_time
		att_req.shift_out_time=shift_end_time
		att_req.shift_type=shift_type
		att_req.delay=late_checkin_mins
		att_req.early=early_checkout_mins
		att_req.overtime=applicable_ot_mins
		att_req.save(ignore_permissions=True)
		return att_req.name

def update_leave_details(leave_name,description):
	leave=frappe.get_doc("Leave Application",leave_name)
	if leave.description:
		new_description=str(description)+'\n '+str(leave.description)
	else:
		new_description=str(description)
	leave.db_set('description', new_description)
	# leave.save(ignore_permissions=True)

def update_attendance_remark(att_name,review_remark):
	att=frappe.get_doc("Attendance",att_name)
	att.db_set('review_remark',review_remark)

# business logic related functions
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
		if emp_out_time<shift_end_time:
			ignore_early_out=shift_type.get("ignore_early_out")
			allowed_early_out=shift_end_time-datetime.timedelta(minutes = ignore_early_out)
			if emp_out_time<allowed_early_out:
				penalty_in_mins=cint(time_diff_in_seconds(shift_end_time,emp_out_time)/60)
	return penalty_in_mins

@frappe.whitelist(allow_guest=True)
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
		# company = frappe.db.get_value("Global Defaults", None, "default_company")
		# default_shift_name=frappe.db.get_value("Company", company, "default_shift_type")	
		# condition_str=' name='+default_shift_name	
		condition_str=' is_default=1'
	
	shift=frappe.db.sql("""select name as shift_type ,start_time ,end_time,
	min_overtime_required,max_overtime_allowed,
	early_checkout_deduction_based_on,ignore_early_out,
	late_checkin_deduction_based_on,working_hours
	from
	 `tabShift Type`
	where {condition_str}""".format(condition_str=condition_str),as_dict=1)
	return shift[0]

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



# Get data for processing
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
	where att_type='in' and att_date = %s and status = 'Pass' and docstatus=1
	group by att_date, employee
	union all
	select date(att_date) as att_date, employee, null in_time,null in_date_time, max(time(att_time)) out_time,max(date(att_time)) as out_date_time
	from `tabEmployee Checkin`
	where att_type='out' and att_date = %s and status = 'Pass' and docstatus=1
	group by att_date, employee
) t on t.employee=emp.name
where 
ifnull(emp.relieving_date, '2199-12-31') >= %s and
emp.salary_slip_based_on='Attendance'
group by att_date, employee""",(date,date,date),as_dict=1)
	return check_in if check_in else None

def total_emp():
	total_emp = frappe.db.sql("""select 
	count(name) as total_emp 
	from `tabEmployee` where status!='Left'
	and salary_slip_based_on='Attendance' """)[0][0]
	return total_emp

def get_holiday_list_for_company():
	holiday_list=''
	company=frappe.db.get_value("Global Defaults", None, "default_company")
	if not holiday_list:
		holiday_list = frappe.get_cached_value('Company',  company,  "default_holiday_list")

	return holiday_list

def is_company_holiday(att_date):

	holiday_list = get_holiday_list_for_company()

	if holiday_list:
		return frappe.get_all('Holiday List', dict(name=holiday_list, holiday_date=att_date)) and True or False


def emp_wo_attendance(att_date):
	emp_wo_attendance = frappe.db.sql("""select count(name) as emp_wo_attendance 
	from `tabEmployee` where name not in(
select distinct(employee) 
from `tabEmployee Checkin` 
where att_date=%s
and status ='Pass' and docstatus=1)
and salary_slip_based_on='Attendance'
and status!='Left'""",att_date)[0][0]
	return emp_wo_attendance


def get_existing_attendance_detail(emp_id,date):
	att_detail=frappe.db.sql("""select 
	name,status,leave_type,checkin_time,checkout_time,review_remark 
	from `tabAttendance` where 
	employee=%s and
	attendance_date=%s and
	docstatus=1
	""",(emp_id,date),as_dict=1)
	return att_detail[0] if bool(att_detail) else None	

def get_leave_of_employee(employee_name,date, status='Approved', docstatus=1):
	leave_detail = frappe.db.sql("""select name as leave_name,leave_type,half_day,half_day_date,leave_approver,from_date
		from `tabLeave Application`
        where employee_name=%(employee_name)s 
			and status = %(status)s 
            and docstatus = %(docstatus)s
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


def get_draft_leave_of_employee(employee_name,date,docstatus=0):
	leave_detail = frappe.db.sql("""select name as leave_name,leave_type,half_day,half_day_date,leave_approver
		from `tabLeave Application`
        where employee_name=%(employee_name)s 
			and status in ("Open", "Approved")
            and docstatus = %(docstatus)s
			and (from_date between %(date)s and %(date)s
				or to_date between %(date)s and %(date)s
				or (from_date < %(date)s and to_date > %(date)s))
	""", {
		"date": date,
		"employee_name": employee_name,
		"docstatus": docstatus
	}, as_dict=1)
	return leave_detail[0] if bool(leave_detail) else None

def attendance_request_exist(emp_id,date,docstatus):
	att_req = frappe.db.sql("""select name from `tabAttendance Request`
where 
employee=%(emp_id)s
and docstatus in %(docstatus)s
and (from_date between %(date)s and %(date)s or to_date between %(date)s and %(date)s or (from_date < %(date)s and to_date > %(date)s))
	""", {
		"emp_id": emp_id,
		"docstatus": docstatus,
		"date": date
	}, as_dict=1)
	return att_req[0]['name'] if att_req else None

#daily pre-check functions
def validate_dates(start_date,end_date):
	if start_date and end_date and (getdate(end_date) < getdate(start_date)):
			frappe.throw(_("To date cannot be before from date"))
	if end_date>getdate(today()) or start_date>getdate(today()):
		frappe.throw(_("Cann't run for future dates"))

def validate_salary_processed_days(start_date,end_date):
	last_processed_pay_slip = frappe.db.sql("""
		select start_date, end_date from `tabSalary Slip`
		where docstatus = 1
		and ((%s between start_date and end_date) or (%s between start_date and end_date))
		order by modified desc limit 1
	""",(end_date,start_date))
	if last_processed_pay_slip:
		frappe.throw(_("Salary already processed for period between {0} and {1}, attendance run cannot be between this date range.").format(formatdate(last_processed_pay_slip[0][0]),
			formatdate(last_processed_pay_slip[0][1])))	

def validate_employee_checkin_status(start_date,end_date):
	employee_checkin_status = frappe.db.sql("""
		select count(*) from `tabEmployee Checkin`
		where docstatus=0
		and att_date between %s and %s
		and status='Fail'
		and remark in (
			"Authorization Token Doesn't Match",
			"Attendance Userid Doesn't Match With Any Employee",
			"Authorization Token Not Found")""",(start_date,end_date))[0][0]
	if employee_checkin_status>0:
		frappe.throw(_("There are  {0} no. of  employee checkin records with fail status.\n (a)Check and change status to Pass and submit it \n OR (b)Check and delete it").format(employee_checkin_status))	


# Main nightly run related function
@frappe.whitelist(allow_guest=True)
def run_nighlty_job():
	if cint(frappe.db.get_value("Attendance Processor", None, "enable_attendance_processor")):
		# runs at midnight
		start_date= add_days(now_datetime().date(), -1)
		run_job(start_date,start_date)
		return

#manual run
@frappe.whitelist(allow_guest=True)
def run_job(start_date,end_date):
	try:
		send_only_failure_emails=cint(frappe.db.get_value("Attendance Processor", None, "send_only_failure_emails"))
		review_count=0
		att_log = frappe.new_doc("Attendance Log")
		print att_log.name
		att_log.run_on = frappe.utils.now()
		att_log.from_date=start_date
		att_log.to_date=end_date
		validate_dates(start_date,end_date)
		validate_salary_processed_days(start_date,end_date)
		validate_employee_checkin_status(start_date,end_date)
		review_count,hr_review_count,admin_review_count=process_employee_checkin_records(start_date,end_date,att_log)
		att_log.run_status = 'Success'
		att_log.review_count=review_count
		att_log.hr_review_count=hr_review_count
		att_log.admin_review_count=admin_review_count
		err_msg=None
	except Exception:
		err_msg= frappe.get_traceback()
		att_log.run_status = 'Fail'
		att_log.review_count=1
		att_log.admin_review_count=1
		att_log.error=err_msg
	finally:
		process_status=att_log.run_status
		att_log.save(ignore_permissions=True)
		att_log.submit()
		print review_count

		if review_count>0:
			process_status='Fail'
		if (send_only_failure_emails==1 and process_status=='Fail') or (send_only_failure_emails==0):
			print process_status
			att_log_url = get_url_to_form("Attendance Log",att_log.name)
			args={
				"run_on":att_log.run_on,
				"run_status":att_log.run_status,
				"review_count":att_log.review_count,
				"hr_review_count":att_log.hr_review_count,
				"admin_review_count":att_log.admin_review_count,
				"from_date":att_log.from_date,
				"to_date":att_log.to_date,
				"att_log_url":att_log_url,
				"error":att_log.error
			}
			notify_auto_attendance_nightly_job_status(args)
			# notify_errors(err_msg,att_log.name,process_status)
		frappe.db.set_value('Attendance Processor', 'Attendance Processor', 'last_run_on', now_datetime())
		frappe.db.set_value('Attendance Processor', 'Attendance Processor', 'attendance_log', att_log.name)
	return
	
@frappe.whitelist(allow_guest=True)
def process_employee_checkin_records(start_date, end_date,att_log):
	
	total_emp_count=total_emp()
	checkin_days = date_diff(end_date,start_date) + 1
	review_count=0
	hr_review_count=0
	admin_review_count=0
	
	for d in range(checkin_days):
		dt = add_days(cstr(getdate(start_date)), d)

		if cint(frappe.db.get_value("Attendance Processor", None, "override_absent_check"))==0:
			is_cmp_holiday=is_company_holiday(dt)
			if is_cmp_holiday==False:
			# stop processing if less than 50% of attendance is present in device on a working day.	
				emp_wo_att_count=emp_wo_attendance(dt)
				per_of_emp_present=((flt(total_emp_count)-flt(emp_wo_att_count))/flt(total_emp_count))*100
				per_of_emp_present = flt(per_of_emp_present,2)
				print 'emp_wo_att_count'
				print emp_wo_att_count
				print 'total_emp_count'
				print total_emp_count
				print 'per_of_emp_present'
				print per_of_emp_present
				if (per_of_emp_present)<51:
					frappe.throw(_("{0} is working day. Device shows data for {1} % of employees. It should be more than 50% and hence cann't run. \n Total Employee are {2}. Absent Employee are {3}").format(dt,per_of_emp_present,total_emp_count,emp_wo_att_count))	

		# fetch all employee device data for particular date
		check_in=get_all_employee_checkin_detail(dt)
		if check_in:
			for emp in check_in:
				
				emp_id=emp['employee']
				emp_att_date=emp['att_date']
				emp_name=emp['emp_name']
				emp_in_time=emp['in_time']
				emp_out_time=emp['out_time']
				present_based_on=emp['present_based_on']

				att_detail=get_existing_attendance_detail(emp_id,dt)
				if att_detail:
					att_name=att_detail['name']
					att_status=att_detail['status']
					att_leave_type=att_detail['leave_type']
					att_checkin_time=att_detail['checkin_time']
					att_checkout_time =att_detail['checkout_time']
					att_review_remark=att_detail['review_remark']



				print 'emp_att_date'
				print emp_att_date
				print 'att_detail'
				print att_detail

				review=0
				reviewer=None

				holiday=is_holiday(emp_id,dt)

				if holiday==True:
					# Holiday so do nothing
					remark=_('Holiday. '+formatdate(dt) +' So, no processing')
				else:
					#It is working day
					present_status=None
					if emp_att_date==None:
						present_status='absent'
					else:
						############################################
						#Do all penalty and overtime calculation
						#get shift detail
						shift=get_shift_detail_of_employee(emp_id,dt)
						shift_type=shift['shift_type']
						shift_start_time=shift['start_time']
						shift_end_time=shift['end_time']
						duration=''
						status='Present'
						late_checkin_mins=0
						early_checkout_mins=0
						applicable_ot_mins=0
						if emp_in_time and emp_out_time:
							duration = emp_out_time - emp_in_time
						else:
							duration=''
						#conditions
						ignore_late_checkin_deduction=emp['ignore_late_checkin_deduction']
						ignore_early_checkout_deduction=emp['ignore_early_checkout_deduction']
						#late checkin
						if ignore_late_checkin_deduction == 0:
							if emp_in_time:
								if emp_in_time>shift_start_time:
									late_checkin_mins = get_late_checkin_penalty(shift_type,emp_in_time)
						# early checkout
						if emp_out_time:
							if ignore_early_checkout_deduction == 0:
								if emp_out_time<shift_end_time:
									early_checkout_mins=get_early_checkout_penalty(shift_type,emp_out_time)
							# overtime
							if emp_out_time>shift_end_time:
								is_eligible_for_attendace_based_overtime_earning=emp['is_eligible_for_attendace_based_overtime_earning']
								if is_eligible_for_attendace_based_overtime_earning==1:
									applicable_ot_mins=calculate_overtime(shift_type,emp_out_time)
						############################################
						if emp_att_date!=None and (emp_in_time!=None and emp_out_time!=None) or (emp_in_time!=None and present_based_on=='Checkin Data Only'):
							present_status='full'
							status='Present'
						elif emp_att_date!=None and (emp_in_time==None and emp_out_time!=None) or (emp_in_time!=None and emp_out_time==None and present_based_on!='Checkin Data Only'):
							present_status='partial'
					if present_status==None:
						frappe.throw(_("Present status is ambiguous for {0} employee and hence cann't run").format(emp_name))

					leave_detail=get_leave_of_employee(emp_name,dt,status='Approved', docstatus=1)
					if leave_detail!=None:
						leave_name=leave_detail["leave_name"]
						leave_approver=leave_detail["leave_approver"]
						half_day=leave_detail["half_day"]
						half_day_date=None
						leave_from_date=leave_detail["from_date"]
						if half_day==1:
							half_day_date=leave_detail["half_day_date"]

					if leave_detail!=None:
					# Leave is there
						print 'half-day'
						print half_day_date
						print getdate(dt)
						print getdate(half_day_date)
						if half_day_date!=None and getdate(dt)==getdate(half_day_date):
							#There is leave with half day and it matches current date
							remark=_('Half-day '+leave_name+ ' on '+ formatdate(half_day_date)+ ' So, no processing')
						else:
							#It is leave with full day
							if present_status=='absent':
								#It is full day leave and there is no attendance data. so it means emp is absent
								remark=_('Absent & existing '+leave_name)
							elif present_status=='full':
								shorten_status,new_shorten_leave=shorten_leave(leave_name,dt,'full')
								print shorten_status
								att_name=create_attendance(emp_id,dt,emp_in_time,emp_out_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,status=status)
								if new_shorten_leave!=None:
									remark=_(att_name+' present created & existing '+leave_name+' is cancelled & new shortened '+ new_shorten_leave+' created')
								elif new_shorten_leave==None:
									remark=_(att_name+' present created & existing '+leave_name+' cancelled')
							
							elif present_status=='partial':
								# there is leave and employee is present. so create AR and update leave remark
								att_req=attendance_request_exist(emp_id,dt,(0,1,2))
								if att_req:
									# It is re-run
									remark=_('Re-run. Emp is '+present_status.capitalize()+' present. Request: '+att_req +' exist for '+leave_name)
								else:
									shorten_status,new_shorten_leave=shorten_leave(leave_name,dt,'partial')
									print 'new_shorten_leave'
									print shorten_status
									print new_shorten_leave
									if shorten_status=='shortened':
										description =present_status.capitalize()+' presence on '+dt+' In: '+str(emp_in_time)+' and Out: '+str(emp_out_time)+ '\n system created LWP'
										delete_draft_status_leave(emp_name,dt,docstatus=0)
										leave_name=create_lwp(emp_id,dt,description,follow_via_email=0)
										explanation='Employee  is '+present_status.capitalize()+' present, hence system created LWP '+leave_name+'.Once it is cancelled, you may submit this request'
										att_req=create_attendance_request(emp_id,dt,emp_in_time,emp_out_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,explanation)
										ar_url = get_url_to_form("Attendance Request",att_req)
										attendance_request_remark='Employee, is partial present. So use your judgement. Honour system created LWP OR cancel LWP and submit '+ar_url+ ' for Overtime/Penalty calculation'
										remark=_(present_status.capitalize()+' present,So created LWP. Honour LWP OR cancel '+leave_name+' & submit '+att_req+' , existing leave is shortened')
										leave_url=get_url_to_form("Leave Application",leave_name)
									elif shorten_status=='no_action':
										explanation='Employee  is '+present_status.capitalize()+' present, There is existing '+leave_name+'.Once it is cancelled, you may submit this request'
										att_req=create_attendance_request(emp_id,dt,emp_in_time,emp_out_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,explanation)
										ar_url = get_url_to_form("Attendance Request",att_req)
										description=dt+' '+present_status.capitalize()+ ' present. In '+str(emp_in_time)+ ' Out '+str(emp_out_time)
										update_leave_details(leave_name,description)
										attendance_request_remark='Employee, is partial present. So use your judgement. Honour existing leave OR cancel leave and submit '+ar_url+ ' for Overtime/Penalty calculation'
										remark=_(present_status.capitalize()+' present, Honour existing leave OR cancel '+leave_name+' & submit '+att_req)
										leave_url=get_url_to_form("Leave Application",leave_name)
									elif shorten_status=='canceled':
										# future date leave is canceled and current date LWP is created
										description =present_status.capitalize()+' presence on '+dt+' In: '+str(emp_in_time)+' and Out: '+str(emp_out_time)+ '\n system created LWP'
										delete_draft_status_leave(emp_name,dt,docstatus=0)
										leave_name=create_lwp(emp_id,dt,description,follow_via_email=0)
										explanation='Employee  is '+present_status.capitalize()+' present, hence system created LWP '+leave_name+'.Once it is cancelled, you may submit this request'
										att_req=create_attendance_request(emp_id,dt,emp_in_time,emp_out_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,explanation)
										ar_url = get_url_to_form("Attendance Request",att_req)
										attendance_request_remark='Employee, is partial present. So use your judgement. Honour system created LWP OR cancel LWP and submit '+ar_url+ ' for Overtime/Penalty calculation'
										remark=_(present_status.capitalize()+' present,So created LWP. Honour LWP OR cancel '+leave_name+' & submit '+att_req+' , existing leave is cancelled')
										leave_url=get_url_to_form("Leave Application",leave_name)				
									#common
									# email inform
									args={
											"employee_name":emp_name,
											"attendance_date":dt,
											"present_status":present_status,
											"checkin_time":str(emp_in_time),
											"checkout_time":str(emp_out_time),
											"leave_url":leave_url
										}
									notify_employee(emp_id,args)
									leave_approver=get_leave_approver(emp_id)
									if leave_approver:
										args["attendance_request_remark"]=attendance_request_remark
										notify_leave_approver(leave_approver,args)
									review=1
									reviewer='HR'	
									review_count +=1
									hr_review_count +=1
									#comm
					elif leave_detail==None:
						# there is no leave	
						if present_status=='absent':
						# there is no leave and emp is absent , so create LWP
							description = 'Employee is absent on '+ dt +' as per device record. Hence system has generated LWP'
							if att_detail==None:
								# before LWP , check for any leave for same date in draft state
								delete_draft_status_leave(emp_name,dt,docstatus=0)
								leave_name=create_lwp(emp_id,dt,description,follow_via_email=1)
								remark=_('Employee is absent on '+ formatdate(dt) +' LWP created '+leave_name)
								review=0
								reviewer=None
							else:
								remark=_('Employee is absent on '+ formatdate(dt) +'& there is '+att_name+ ' with status '+att_status)
								review=1
								reviewer='Admin'
								review_count +=1
								admin_review_count +=1
						elif present_status=='full':
							if att_detail==None :
								# there is no existing attendance
								att_name=create_attendance(emp_id,dt,emp_in_time,emp_out_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,status=status)
								remark=_('Attendance with status Present is created '+att_name)
							else:
								remark=_('Re-run. Existing attendance '+str(att_name)+ ' status '+str(att_status))
						elif present_status=='partial':
							att_req=attendance_request_exist(emp_id,dt,(0,1,2))
							if att_req!=None:
								remark=_('Re-run. AR '+str(att_req)+ ' exist for partial presence')
							elif att_req==None :
								description =_(present_status.capitalize()+' presence on '+dt+' In: '+str(emp_in_time)+' and Out: '+str(emp_out_time)+ '\n system created LWP')
								# before LWP , check for any leave for same date in draft state
								delete_draft_status_leave(emp_name,dt,docstatus=0)
								if att_detail==None:
									leave_name=create_lwp(emp_id,dt,description,follow_via_email=0)
									explanation='Employee  is '+present_status.capitalize()+' present, hence system created LWP '+leave_name+'.Once it is cancelled, you may submit this request'
									att_req=create_attendance_request(emp_id,dt,emp_in_time,emp_out_time,duration,shift_start_time,shift_end_time,shift_type,late_checkin_mins,early_checkout_mins,applicable_ot_mins,explanation)
									ar_url = get_url_to_form("Attendance Request",att_req)
									# email inform
									leave_url=get_url_to_form("Leave Application",leave_name)
									args={
											"employee_name":emp_name,
											"attendance_date":dt,
											"present_status":present_status,
											"checkin_time":str(emp_in_time),
											"checkout_time":str(emp_out_time),
											"leave_url":leave_url
										}
									notify_employee(emp_id,args)
									leave_approver=get_leave_approver(emp_id)
									if leave_approver:
										attendance_request_remark='Employee, is partial present. So use your judgement. Honour system created LWP OR cancel LWP and submit '+ar_url+ ' for Overtime/Penalty calculation'
										args["attendance_request_remark"]=attendance_request_remark
										notify_leave_approver(leave_approver,args)
									remark=present_status.capitalize()+' present,So created LWP. Honour LWP OR [cancel '+leave_name+' & submit '+att_req+']'
									review=1
									reviewer='HR'	
									review_count +=1
									hr_review_count +=1
								else:
									remark=_('Employee is partial present & there is '+att_name+ ' with status '+att_status)
									review=1
									reviewer='Admin'
									review_count +=1
									admin_review_count +=1
				print emp_name
				print 'emp_in_time'
				print emp_in_time
				print 'emp_out_time'
				print emp_out_time
				if emp_in_time == None:
					emp_in_time=""
				if emp_out_time == None:
					emp_out_time=""				
				att_log_entry={
				'emp':emp_name,
				'date':dt,
				'in':emp_in_time,
				'out':emp_out_time
				}
				attedance_record=get_existing_attendance_detail(emp_id,dt)
				if attedance_record:
					print attedance_record['name']
					att_log_entry['att']=attedance_record['name']
				leave_record=get_leave_of_employee(emp_name,dt,status='Approved', docstatus=1)
				if leave_record:
					print leave_record['leave_name']
					att_log_entry['leave']=leave_record['leave_name']
				if 'att_req' in locals():
					print att_req
					att_log_entry['att_req']=att_req
				print remark
				print review
				att_log_entry['remark']=remark
				att_log_entry['review']=review
				att_log_entry['reviewer']=reviewer
				print '------------'

				if review==1:
					att_log.append("att_log_entry_fail",att_log_entry)
				else:
					att_log.append("att_log_entry_success",att_log_entry)
				#Reset all variables
				emp=None
				att_detail=None
				att_name=None
				leave_detail=None
				leave_name=None
				att_req=None
				remark=None
				review=None
				reviewer=None
				att_log_entry={}
				present_status=None
	return review_count,hr_review_count,admin_review_count


#Email related functions
def notify_employee(emp_id,args):
	employee = frappe.get_doc("Employee", emp_id)
	if not employee.user_id:
		return

	# template = frappe.db.get_single_value('HR Settings', 'attendance_reconciliation_information_template')
	# if not template:
	# 	frappe.msgprint(_("Please set default template for Attendance Reconciliation Information in HR Settings."))
	# 	return
	template='Attendance Reconciliation Information'
	email_template = frappe.get_doc("Email Template", template)
	message = frappe.render_template(email_template.response, args)
	print message
	notify({
		# for post in messages
		"message": message,
		"message_to": employee.user_id,
		# for email
		"subject": email_template.subject,
		"notify": "employee"
	})

def notify_leave_approver(leave_approver,args):
		# template = frappe.db.get_single_value('HR Settings', 'attendance_reconciliation_request_template')
		# if not template:
		# 	frappe.msgprint(_("Please set default template for Attendance Reconciliation Request in HR Settings."))
		# 	return
		template='Attendance Reconciliation Request'
		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)
		print message
		notify({
			# for post in messages
			"message": message,
			"message_to": leave_approver,
			# for email
			"subject": email_template.subject
		})

def notify(args):
	args = frappe._dict(args)
	# args -> message, message_to, subject
	contact = args.message_to
	if not isinstance(contact, list):
		if not args.notify == "employee":
			contact = frappe.get_doc('User', contact).email or contact

	sender      	    = dict()
	sender['email']     = frappe.get_doc('User', frappe.session.user).email
	sender['full_name'] = frappe.utils.get_fullname(sender['email'])
	print sender['email']
	print contact
	print args.subject

	try:
		frappe.sendmail(
			recipients = contact,
			sender = sender['email'],
			subject = args.subject,
			message = args.message,
		)
		frappe.msgprint(_("Email sent to {0}").format(contact))
	except frappe.OutgoingEmailError:
		pass


def notify_auto_attendance_nightly_job_status(args):
	if frappe.db.get_value("Attendance Processor", None, "send_job_email_to"):
		recipients = split_emails(frappe.db.get_value("Attendance Processor", None, "send_job_email_to"))
	nightly_job_notification_template = frappe.db.get_value("Attendance Processor", None, "nightly_job_notification_template")
	email_template = frappe.get_doc("Email Template", nightly_job_notification_template)
	message = frappe.render_template(email_template.response, args)
	print message
	print recipients
	notify({
		# for post in messages
		"message": message,
		"message_to": recipients,
		# for email
		"subject": email_template.subject
	})

def notify_errors(exceptions,att_log,status):
	
	print att_log
	att_log_url = get_url_to_form("Attendance Log",att_log)
	print att_log_url
	print exceptions
	subject = "[Important] [ERPNext] Auto Attendance System Error"
	if status=='Fail' and exceptions!=None:
		content = """Dear System Manager,

	An error occured while processing attendance of employees.

	Attendance Log link %s

	Please rectify these issues:
	---
	<pre>
	%s
	</pre>
	---
	Regards,
	Administrator""" % (att_log_url,"\n\n".join(exceptions))
	elif status=='Fail' and exceptions==None :
		content = """Dear System Manager,

	There are failure review comments which needs to be checked.

	Attendance Log link %s
	---
	Regards,
	Administrator""" % (att_log_url)		
	else:
		content = """Dear System Manager,

	Processing of attendance was successful.

	Attendance Log link %s
	---
	Regards,
	Administrator""" % (att_log_url)		

	if frappe.db.get_value("Attendance Processor", None, "send_job_email_to"):
		recipients = split_emails(frappe.db.get_value("Attendance Processor", None, "send_job_email_to"))
		frappe.sendmail(recipients=recipients, subject=subject, message=content)

	# from frappe.email import sendmail_to_system_managers
	# sendmail_to_system_managers(subject, content)


# function to check if there leaves beyond payroll end date
@frappe.whitelist(allow_guest=True)
def validate_employee_leave_on_salary_boundary(salary_start_date,salary_end_date):
    employees_with_leaves_on_payroll_boundary=[]
    employees_with_leaves_on_payroll_boundary = frappe.db.sql("""select
    name, employee_name 
    from `tabLeave Application`
    where status='Approved' 
    and docstatus=1
	and (from_date between %(salary_start_date)s  and %(salary_end_date)s)
	and to_date>%(salary_end_date)s
	order by employee_name
	""",
	{
	"salary_start_date":salary_start_date,
	"salary_end_date":salary_end_date
	},as_dict=1)
    return employees_with_leaves_on_payroll_boundary

@frappe.whitelist(allow_guest=True)
def split_multiple_leaves(salary_start_date,salary_end_date):
	leaves_on_payroll_boundary=validate_employee_leave_on_salary_boundary(salary_start_date,salary_end_date)
	print leaves_on_payroll_boundary
	if len(leaves_on_payroll_boundary)>0:
		for leave in leaves_on_payroll_boundary:
			print leave['name'],salary_end_date
			split_leave(leave['name'],salary_end_date,split_type='two_part')
	return validate_employee_leave_on_salary_boundary(salary_start_date,salary_end_date)


def shorten_leave(existing_leave_name,current_date,present_status):
	# shorten_status = 'shortened','canceled','no_action'
	# get_existing_leave_details
	leave=frappe.get_doc('Leave Application',existing_leave_name)
	if leave:
		new_half_day=None
		new_half_day_date=None
		if(getdate(leave.from_date)<getdate(current_date)):
			#new leave data
			new_end_date=getdate(add_days((getdate(current_date)), -1))
			new_start_date=leave.from_date
			if leave.half_day_date:
				if getdate(leave.half_day_date)<=getdate(new_end_date):
					new_half_day=leave.half_day
					new_half_day_date=leave.half_day_date
			new_no_of_leave_days=get_number_of_leave_days(leave.employee, leave.leave_type,new_start_date,new_end_date,new_half_day,new_half_day_date)
			if new_no_of_leave_days>0:
				leave.db_set('description', _('Leave is cancelled by system. Employee has '+present_status.capitalize()+ ' turned up on '+str(current_date)+ ' New leave was created for previous period'))
				leave.cancel()
				#new shortened leave
				new_leave=frappe.copy_doc(leave)
				new_leave.from_date=new_start_date
				new_leave.to_date=new_end_date
				new_leave.half_day=new_half_day
				new_leave.half_day_date=new_half_day_date
				new_leave.follow_via_email=0
				new_leave.status='Approved'
				new_leave.posting_date=today()
				new_leave.description='Shorten version of '+existing_leave_name
				new_leave.save(ignore_permissions=True)
				new_leave.submit()
				shorten_status = 'shortened'
				return shorten_status,new_leave.name
			elif new_no_of_leave_days==0:
				if present_status=='partial':
					shorten_status = 'no_action'
					return shorten_status,None
				elif present_status=='full':
					leave.db_set('description', _('Leave is cancelled by system. Employee has fully turned up on '+str(current_date)+', No leave created'))
					leave.cancel()
					shorten_status='canceled'
					return shorten_status,None			
		elif(getdate(leave.from_date)==getdate(current_date)):
			if present_status=='full':
				leave.db_set('description', _('Leave is cancelled by system. Employee has '+ present_status.capitalize()+' turned up on '+str(current_date)+', No leave created'))
				leave.cancel()
				shorten_status='canceled'
				return shorten_status,None
			elif present_status=='partial':
				if(getdate(leave.to_date)>getdate(current_date)):
					new_start_date=getdate(add_days((getdate(current_date)), 1))
					new_end_date=leave.to_date
					if leave.half_day_date:
						if getdate(leave.half_day_date)>=getdate(new_start_date):
							new_half_day=leave.half_day
							new_half_day_date=leave.half_day_date
					new_no_of_leave_days=get_number_of_leave_days(leave.employee, leave.leave_type,new_start_date,new_end_date,new_half_day,new_half_day_date)
					if new_no_of_leave_days>0:
						leave.db_set('description', _('Leave is cancelled by system. Employee has '+ present_status.capitalize()+' turned up on '+str(current_date)+', LWP is created for partial presence'))
						leave.cancel()
						shorten_status='canceled'
						return shorten_status,None
					elif new_no_of_leave_days==0:
						shorten_status='no_action'
						return shorten_status,None
				else:
					shorten_status='no_action'
					return shorten_status,None

def shorten_leave1(leave_name,split_date,present_status):
	leave=frappe.get_doc('Leave Application',leave_name)
	if leave:
		first_half_day=None
		first_half_day_date=None
		first_total_leave_days=0
		first_start_date=leave.from_date
		first_end_date=split_date
		if leave.half_day_date:
			if getdate(leave.half_day_date)<=getdate(split_date):
				first_half_day=leave.half_day
				first_half_day_date=leave.half_day_date
		first_total_leave_days = get_number_of_leave_days(leave.employee, leave.leave_type,first_start_date,first_end_date,first_half_day,first_half_day_date)
		print first_total_leave_days
		print 'first_total_leave_days'
		present_on=cstr(add_days(cstr(getdate(split_date)), 1))
		if (first_total_leave_days==0 and present_status=='full'):
			leave.db_set('description', _('Cancelled by system as employee has fully turned up during leave period on '+present_on+', No leave created'))
			print 'cancelled by system as employee is turned up during leave period'
			#leave.flags.ignore_validate = True
			leave.cancel()

		if first_total_leave_days>0 and present_status=='full':
			leave.db_set('description', _('Cancelled by system as employee has fully turned up on '+present_on+ ' In lieu, new shortened leave was created'))
			print 'cancelled by system as employee is turned up during leave period'
			#leave.flags.ignore_validate = True
			leave.cancel()
		if (first_total_leave_days>0 and present_status=='partial'):
			leave.db_set('description', _('Cancelled by system as employee has partially turned up on '+present_on+ ' In lieu, new shortened leave was created'))
			print 'cancelled by system as employee is turned up during leave period'
			#leave.flags.ignore_validate = True
			leave.cancel()
		if (first_total_leave_days==0 and present_status=='partial' and getdate(first_start_date)==getdate(present_on)):
		#Employee partially turns up on first day of leave period
			leave.db_set('description', _('Cancelled by system as employee has partially turned up on '+present_on+ ' Existing leave is cancelled as turned up on first date'))
			print 'cancelled by system as employee is turned up during leave period'
			#leave.flags.ignore_validate = True
			leave.cancel()
		if (first_total_leave_days > 0) :
			new_leave=frappe.copy_doc(leave)
			new_leave.from_date=first_start_date
			new_leave.to_date=first_end_date
			new_leave.half_day=first_half_day
			new_leave.half_day_date=first_half_day_date
			new_leave.follow_via_email=0
			new_leave.status='Approved'
			new_leave.posting_date=today()
			new_leave.description=_('Shorten version of ')+leave_name
			new_leave.save(ignore_permissions=True)
			new_leave.submit()
			return new_leave.name
		else:
			return None


def split_leave(leave_name,split_date,split_type='two_part'):
	leave=frappe.get_doc('Leave Application',leave_name)
	if leave:
		first_half_day=None
		first_half_day_date=None
		second_half_day=None
		second_half_day_date=None
		first_total_leave_days=0
		second_total_leave_days=0
		if split_type=='two_part':
			first_start_date=leave.from_date
			first_end_date=split_date
			first_half_day=None
			first_half_day_date=None

			second_start_date=add_days(cstr(getdate(split_date)), 1)
			second_end_date=leave.to_date
			second_half_day=None
			second_half_day_date=None

			if leave.half_day_date:
				if getdate(leave.half_day_date)<=getdate(first_end_date):
					first_half_day=leave.half_day
					first_half_day_date=leave.half_day_date
				elif getdate(leave.half_day_date)>=getdate(second_start_date):
					second_half_day=leave.half_day
					second_half_day_date=leave.half_day_date
		
			first_total_leave_days = get_number_of_leave_days(leave.employee, leave.leave_type,first_start_date,first_end_date,first_half_day,first_half_day_date)
			second_total_leave_days = get_number_of_leave_days(leave.employee, leave.leave_type,second_start_date,second_end_date,second_half_day,second_half_day_date)

			if first_total_leave_days>0 or second_total_leave_days>0: 
				leave.db_set('description', 'cancelled by system, and splited into 2 leaves as leave period was overlapping payroll dates')
				leave.flags.ignore_validate = True
				leave.cancel()
			if (split_type=='two_part' and first_total_leave_days > 0):
				new_leave=frappe.copy_doc(leave)
				new_leave.from_date=first_start_date
				new_leave.to_date=first_end_date
				new_leave.half_day=first_half_day
				new_leave.half_day_date=first_half_day_date
				new_leave.follow_via_email=0
				new_leave.status='Approved'
				new_leave.posting_date=today()
				new_leave.description='Split of '+leave_name +' first part'
				new_leave.save(ignore_permissions=True)
				new_leave.submit()
			if split_type=='two_part' and second_total_leave_days > 0:
				new_leave=frappe.copy_doc(leave)
				new_leave.from_date=second_start_date
				new_leave.to_date=second_end_date
				new_leave.half_day=second_half_day
				new_leave.half_day_date=second_half_day_date
				new_leave.follow_via_email=0
				new_leave.status='Approved'
				new_leave.posting_date=today()
				new_leave.description='Split of '+leave_name+ ' second part'
				new_leave.save(ignore_permissions=True)
				new_leave.submit()

def get_leave_with_missing_attendance(date):
	leave_wo_attendance= frappe.db.sql("""select employee,leave_type,half_day_date
		from `tabLeave Application`
		where docstatus=1
		and status='Approved'
		and %s between from_date and to_date
		and employee not in (select employee from `tabAttendance`
		where attendance_date=%s)""",(date,date),as_dict=1)
	return leave_wo_attendance if leave_wo_attendance else None

def create_att_for_leave(date):
	att_req=get_leave_with_missing_attendance(date)
	print 'att_req'
	print att_req
	if att_req:
		for att in att_req:
			#date = dt.strftime("%Y-%m-%d")
			doc = frappe.new_doc("Attendance")
			doc.employee = att['employee']
			doc.attendance_date = date
			doc.company = frappe.get_value('Employee', att['employee'], 'company')
			doc.leave_type = att['leave_type']
			doc.status = "Half Day" if date == att['half_day_date'] else "On Leave"
			doc.review_remark='Inserted by system night job'
			doc.save(ignore_permissions=True)
			# doc.flags.ignore_validate = True
			# doc.insert(ignore_permissions=True)
			doc.submit()
	return

def delete_draft_status_leave(emp_name,dt,docstatus=0):
	# before LWP , check for any leave for same date in draft state
	draft_leave=get_draft_leave_of_employee(emp_name,dt,docstatus=0)
	if draft_leave:
		draft_leave_name=draft_leave["leave_name"]
		doc=frappe.get_doc('Leave Application',draft_leave_name)
		doc.description=_('Draft leave deleted by attendance system. As per rule')
		doc.save(ignore_permissions=True)
		frappe.delete_doc('Leave Application',draft_leave_name)