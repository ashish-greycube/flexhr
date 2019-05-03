# -*- coding: utf-8 -*-
# Copyright (c) 2018, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe import _
from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words, getdate
from frappe.model.document import Document
from erpnext.hr.doctype.payroll_entry.payroll_entry import get_start_end_dates
from flexhr.flex_hr.attendance_controller import get_shift_detail_of_employee
from erpnext import get_default_company

class AdditionalSalaryEntry(Document):
	def validate(self):
		if self.start_date <= self.posting_date  <= self.end_date:
			pass
		else:
			frappe.throw(_('Posting date {0} should be between {1} and {2}').format(self.posting_date,self.start_date,self.end_date))
	def get_open_attendance_request(self):
		open_attendance_request=[]
		open_attendance_request = frappe.db.sql("""select name,employee_name from `tabAttendance Request`
						where docstatus=0
						and (from_date between %(salary_start_date)s  and %(salary_end_date)s)
						and (to_date between %(salary_start_date)s  and %(salary_end_date)s)
						order by employee_name
		""",
		{
		"salary_start_date":self.start_date,
		"salary_end_date":self.end_date
		},as_dict=1)
		return open_attendance_request

	def get_open_overtime_application(self):
		open_overtime_application=[]
		open_overtime_application = frappe.db.sql("""select name,ot_date as date, employee_name from `tabOvertime Application`
						where docstatus=0
						and (ot_date between %(salary_start_date)s  and %(salary_end_date)s)
						order by employee_name
		""",
		{
		"salary_start_date":self.start_date,
		"salary_end_date":self.end_date
		},as_dict=1)
		return open_overtime_application

	def on_submit(self):
		self.create_additional_salary_slips()

	def check_mandatory(self):
		for fieldname in ['company', 'start_date', 'end_date']:
			if not self.get(fieldname):
				frappe.throw(_("Please set {0}").format(self.meta.get_label(fieldname)))


	def get_joining_releiving_condition(self):
		cond = """
			and ifnull(t1.date_of_joining, '0000-00-00') <= '%(end_date)s'
			and ifnull(t1.relieving_date, '2199-12-31') >= '%(start_date)s'
		""" % {"start_date": self.start_date, "end_date": self.end_date}
		return cond

	def get_filter_condition(self):
		self.check_mandatory()

		cond = ''
		for f in ['company', 'branch', 'department', 'designation','employee']:
			if self.get(f):
				cond += " and t1." + f + " = '" + self.get(f).replace("'", "\'") + "'"

		return cond

	def get_emp_list(self):
		"""
			Returns list of active employees based on selected criteria
			and for which salary structure exists
		"""
		cond = self.get_filter_condition()
		cond += self.get_joining_releiving_condition()
		print cond
		#condition = 'order by modified desc LIMIT 1'
		condition = ''
		if self.payroll_frequency:
			condition = """and SS.payroll_frequency = '%(payroll_frequency)s'"""% {"payroll_frequency": self.payroll_frequency}
		print 'inside get_emp_list'
		# is_included_for_delay_and_overtime flag check at child table i.e. salary detail level
		sal_struct = frappe.db.sql_list("""
				select distinct(SS.name)  from `tabSalary Structure` SS
					inner join `tabSalary Detail` SD
					on SS.name=SD.parent
				where
					SD.parenttype='Salary Structure'
					and SD.is_included_for_delay_and_overtime=1
					and SS.docstatus = 1
					and SS.is_active = 'Yes'
					and SS.company = %(company)s 
					{condition}""".format(condition=condition),
				{"company": self.company})

		# is_included_for_delay_and_overtime flag check at component level
		# sal_struct = frappe.db.sql_list("""
		# 		select distinct(SS.name)  from `tabSalary Structure` SS
		# 			inner join `tabSalary Detail` SD
		# 				on SS.name=SD.parent
		# 			inner join `tabSalary Component` SC
		# 				on SD.salary_component=SC.name
		# 			where
		# 				SD.parenttype='Salary Structure'
		# 				and SC.is_included_for_delay_and_overtime=1
		# 				and SS.docstatus = 1
		# 				and SS.is_active = 'Yes'
		# 				and SS.company = %(company)s 
		# 			{condition}""".format(condition=condition),
		# 		{"company": self.company})
		print 'sal_struct'
		print sal_struct
		if sal_struct:

			# cond += "and t2.salary_structure IN %(sal_struct)s "
			# cond += "and %(from_date)s >= t2.from_date"
			# #original multiple ss
			# emp_list = frappe.db.sql("""
			# 	select
			# 		t1.name as employee, t1.employee_name, t1.department, t1.designation,
			# 		t2.salary_structure,t2.base
			# 	from
			# 		`tabEmployee` t1, `tabSalary Structure Assignment` t2
			# 	where
			# 		t1.name = t2.employee
			# 		and t2.docstatus = 1
			# %s order by t2.from_date desc
			
			# """ % cond, {"sal_struct": tuple(sal_struct), "from_date": self.end_date}, as_dict=True)

			
			# single ss only
			cond += "and t2.salary_structure IN %(sal_struct)s "
			cond += "and %(from_date)s >= t2.from_date and not exists (	select 1 from `tabSalary Structure Assignment` t3 where t3.name <> t2.name	and t3.employee = t2.employee and t3.from_date > t2.from_date and   %(from_date)s >=t3.from_date )	order by t2.from_date desc"
			print cond
			emp_list = frappe.db.sql("""
				select t1.name as employee, t1.employee_name, t1.department, t1.designation,
					t2.salary_structure, t2.base
				from  `tabEmployee` t1,`tabSalary Structure Assignment` t2
    			where 
					t2.docstatus = 1    
    				and t1.name = t2.employee
					%s
			""" % cond, {"sal_struct": tuple(sal_struct), "from_date": self.end_date}, as_dict=True)	
			print 'emp_list'
			print emp_list
			return emp_list

	def create_additional_salary_slips(self):
		company = get_default_company()	
		fhr_delay_component=frappe.get_value('Company', company, 'fhr_delay_component')
		fhr_overtime_component=frappe.get_value('Company', company, 'fhr_overtime_component')
		if (not fhr_delay_component) or (not fhr_overtime_component):
			frappe.throw(_("Delay/Overtime component are not defined in default company"))
		for d in self.employees:
			if d.irregular_checkin_checkout_deduction>0:
				ad_sal = frappe.new_doc("Additional Salary")
				ad_sal.employee=d.employee
				ad_sal.salary_component=fhr_delay_component
				ad_sal.amount=d.irregular_checkin_checkout_deduction
				ad_sal.payroll_date=self.posting_date
				ad_sal.overwrite_salary_structure_amount=0
				ad_sal.save()
				ad_sal.submit()
			if d.overtime_earning>0:
				ad_sal = frappe.new_doc("Additional Salary")
				ad_sal.employee=d.employee
				ad_sal.salary_component=fhr_overtime_component
				ad_sal.amount=d.overtime_earning
				ad_sal.payroll_date=self.posting_date
				ad_sal.overwrite_salary_structure_amount=0
				ad_sal.save()
				ad_sal.submit()


	def fill_employee_details(self):
		self.set('employees', [])
		employees = self.get_emp_list()
		if not employees:
			frappe.throw(_("No employees for the mentioned criteria"))
		for d in employees:
			result= get_attendance_details(d.employee,self.start_date,self.end_date)
			if result != None:
				delay_amount,ot_amount=calculate_component_amounts(d.employee,self.company,d.salary_structure,d.base,result.late_checkin,result.early_checkout,result.overtime,self.start_date)
				print 'attendance'
				print d.employee,d.salary_structure
				ans={
					'employee':d.employee,
					'late_checkin':result.late_checkin,
					'early_checkout':result.early_checkout,
					'irregular_checkin_checkout_deduction':delay_amount,
					'overtime':result.overtime,
					'overtime_earning':ot_amount
				}
				self.append('employees',ans)


			## overtime application calculation
		for d in employees:
			result=get_overtime_application_details(d.employee,self.start_date,self.end_date)
			if result != None:
				delay_amount,ot_amount=calculate_component_amounts(d.employee,self.company,d.salary_structure,d.base,result.late_checkin,result.early_checkout,result.overtime,self.start_date)
			if result != None:
				print 'OT application'
				print d.employee,d.salary_structure
				ans={
					'employee':d.employee,
					'late_checkin':result.late_checkin,
					'early_checkout':result.early_checkout,
					'irregular_checkin_checkout_deduction':delay_amount,
					'overtime':result.overtime,
					'overtime_earning':ot_amount
				}
				self.append('employees',ans)


		self.number_of_employees = len(employees)

def get_data_for_eval(employee,salary_structure):
	'''Returns data for evaluating formula'''
	data = frappe._dict()
	_salary_structure_doc = frappe.get_doc('Salary Structure', salary_structure)

	data.update(frappe.get_doc("Employee", employee).as_dict())
	data.update(_salary_structure_doc.as_dict())

	# set values for components
	salary_components = frappe.get_all("Salary Component", fields=["salary_component_abbr"])
	for sc in salary_components:
		data.setdefault(sc.salary_component_abbr, 0)

	for key in ('earnings', 'deductions'):
		for d in _salary_structure_doc.get(key):
			data[d.abbr] = d.amount

	return data

def calculate_component_amounts(employee,company,salary_structure,base,late_checkin,early_checkout,overtime,salary_start_date):
		_salary_structure_doc = frappe.get_doc('Salary Structure', salary_structure)
		data = get_data_for_eval(employee,salary_structure)
		total_amt=0
		for key in ('earnings', 'deductions'):
			for struct_row in _salary_structure_doc.get(key):
				amount = eval_condition_and_formula(struct_row, base,data)
				total_amt=amount+total_amt
				
		per_minute_amount_for_additional_salary_based_on = frappe.db.get_value("Company", company, "per_minute_amount_for_additional_salary_based_on")
		if per_minute_amount_for_additional_salary_based_on=='Fixed Days':
			no_of_fixed_days=frappe.db.get_value("Company", company, "no_of_fixed_days")
		working_hours=get_shift_detail_of_employee(employee,salary_start_date)['working_hours']
		per_min=total_amt/cint(no_of_fixed_days)/flt(working_hours)/60
		total_delay_min=late_checkin+early_checkout
		delay_amount=per_min*total_delay_min
		ot_factor = frappe.db.get_value("Company", company, "overtime_earning_factor")
		ot_amount=(per_min)*overtime *ot_factor
		return delay_amount,ot_amount

def get_overtime_application_details(employee,start_date,end_date):
	att_list = frappe.db.sql("""select 
0 as late_checkin,
0 as early_checkout,
ifnull(sum(approved_ot_mins),0) as overtime
from `tabOvertime Application`
where
status='Approved' and 
approved_ot_mins >0 and
docstatus=1 and
employee = %s and
ot_date between %s and %s""", (employee,start_date, end_date), as_dict=True)
	return att_list[0] if att_list[0]['overtime']>0 else None

def get_attendance_details(employee,start_date,end_date):
	att_list = frappe.db.sql("""select 
	ifnull(sum(delay),0) as late_checkin,
	ifnull(sum(early),0) as early_checkout,
	ifnull(sum(overtime),0) as overtime
from `tabAttendance`
where
employee = %s
and status='Present'
and docstatus=1
and date(attendance_date) between %s and %s""", (employee,start_date, end_date), as_dict=True)
	return att_list[0] if (att_list[0]['late_checkin']>0 or att_list[0]['early_checkout']>0 or att_list[0]['overtime']>0) else None

def eval_condition_and_formula(d,base, data):
	whitelisted_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"date": datetime.date,
			"getdate": getdate
		}
	try:
		
		condition = d.condition.strip() if d.condition else None
		if condition:
			if not frappe.safe_eval(condition, whitelisted_globals, data):
				return None
		amount = d.amount
		
		if d.amount_based_on_formula:
			formula = d.formula.strip() if d.formula else None
			
			data.base=base
			if formula:
				amount = frappe.safe_eval(formula, whitelisted_globals, data)
				
		if amount:
			data[d.abbr] = amount

		return amount

	except NameError as err:
		frappe.throw(("Name error: {0}".format(err)))
	except SyntaxError as err:
		frappe.throw(("Syntax error in formula or condition: {0}".format(err)))
	except Exception as e:
		frappe.throw(("Error in formula or condition: {0}".format(e)))
		raise