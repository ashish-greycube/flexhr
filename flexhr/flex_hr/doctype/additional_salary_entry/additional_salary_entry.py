# -*- coding: utf-8 -*-
# Copyright (c) 2018, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe import _
from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words, getdate
from frappe.model.document import Document

class AdditionalSalaryEntry(Document):

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
		for f in ['company', 'branch', 'department', 'designation']:
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

		condition = 'order by modified desc LIMIT 1'
	
		sal_struct = frappe.db.sql_list("""
				select
					name from `tabSalary Structure`
				where
					docstatus = 1 and
					is_active = 'Yes'
					and company = %(company)s 
					{condition}""".format(condition=condition),
				{"company": self.company})
		if sal_struct:
			cond += "and t2.salary_structure IN %(sal_struct)s "
			cond += "and %(from_date)s >= t2.from_date"
			emp_list = frappe.db.sql("""
				select
					t1.name as employee, t1.employee_name, t1.department, t1.designation,
					t2.salary_structure,t2.base
				from
					`tabEmployee` t1, `tabSalary Structure Assignment` t2
				where
					t1.name = t2.employee
					and t2.docstatus = 1
			%s order by t2.from_date desc 
			
			""" % cond, {"sal_struct": tuple(sal_struct), "from_date": self.end_date}, as_dict=True)
			print 'emp_list'
			print cond
			print sal_struct
			print self.end_date
			print emp_list
			return emp_list



	def create_additional_salary_slips(self):
		print 'create'
		print self
		for d in self.employees:
			if d.irregular_checkin_checkout_deduction>0:
				print 'delay_amount'
				ad_sal = frappe.new_doc("Additional Salary")
				ad_sal.employee=d.employee
				ad_sal.salary_component='Delay Penalty'
				ad_sal.amount=d.irregular_checkin_checkout_deduction
				ad_sal.payroll_date=self.posting_date
				ad_sal.overwrite_salary_structure_amount=0
				ad_sal.save()
				ad_sal.submit()
			if d.overtime_earning>0:
				print 'overtime_earning'
				ad_sal = frappe.new_doc("Additional Salary")
				ad_sal.employee=d.employee
				ad_sal.salary_component='Overtime'
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
			print result
			# get all submitted overtime application
			if result != None:
				result=get_overtime_application_details(d.employee,self.start_date,self.end_date)
				print result

			delay_amount,ot_amount=calculate_component_amounts(d.employee,self.company,d.salary_structure,d.base,result.late_checkin,result.early_checkout,result.overtime)
			# ear=frappe.get_doc('Salary Structure', d.salary_structure)
		#	print ear.get("earnings")[0]
			# print comp
			if result != None:
				ans={
					'employee':d.employee,
					'late_checkin':result.late_checkin,
					'early_checkout':result.early_checkout,
					'irregular_checkin_checkout_deduction':delay_amount,
					'overtime':result.overtime,
					'overtime_earning':ot_amount
				}
				# print d.employee
				# ans.update({'employee',d.employee})
				# ans.update({'late_checkin',result.late_checkin})
				# ans.update({'early_checkout',result.early_checkout})
				# ans.update({'irregular_checkin_checkout_deduction',delay_amount})
				# ans.update({'overtime',result.overtime})
				# ans.update({'overtime_earning',ot_amount})
				
				# ans1=Merge(d.employee+result.late_checkin+result.early_checkout)
				print ans
			 	# d.append(result)
			self.append('employees',ans)
			# print d


		self.number_of_employees = len(employees)

def get_data_for_eval(employee,salary_structure):
	'''Returns data for evaluating formula'''
	data = frappe._dict()
	_salary_structure_doc = frappe.get_doc('Salary Structure', salary_structure)
	# data.update(frappe.get_doc("Salary Structure Employee",
		# {"employee": employee, "parent": salary_structure}).as_dict())

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

def calculate_component_amounts(employee,company,salary_structure,base,late_checkin,early_checkout,overtime):
		_salary_structure_doc = frappe.get_doc('Salary Structure', salary_structure)
		data = get_data_for_eval(employee,salary_structure)
		# print data
		total_amt=0
		for key in ('earnings', 'deductions'):
			for struct_row in _salary_structure_doc.get(key):
				amount = eval_condition_and_formula(struct_row, base,data)
				print 'each'
				print amount
				total_amt=amount+total_amt
				
		per_minute_amount_for_additional_salary_based_on = frappe.db.get_value("Company", company, "per_minute_amount_for_additional_salary_based_on")
		if per_minute_amount_for_additional_salary_based_on=='Fixed Days':
			no_of_fixed_days=frappe.db.get_value("Company", company, "no_of_fixed_days")
		per_min=total_amt/cint(no_of_fixed_days)/8/60
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
	print 'OT'
	print employee
	print start_date
	print end_date
	print att_list
	return att_list[0] if att_list else None


def get_attendance_details(employee,start_date,end_date):
	att_list = frappe.db.sql("""select 
	ifnull(sum(delay),0) as late_checkin,
	ifnull(sum(early),0) as early_checkout,
	ifnull(sum(overtime),0) as overtime
from `tabAttendance`
where
employee = %s
and status='Present'
and date(attendance_date) between %s and %s""", (employee,start_date, end_date), as_dict=True)
	return att_list[0] if att_list else None

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