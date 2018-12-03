# -*- coding: utf-8 -*-
# Copyright (c) 2018, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.hr.utils import set_employee_name

class OvertimeApplication(Document):
	
	def validate_duplicate_record(self):
		res = frappe.db.sql("""select name from `tabOvertime Application` where employee = %s and ot_date = %s
			and name != %s and docstatus < 2""",
			(self.employee, self.ot_date, self.name))
		if res:
			frappe.throw(_("Overtime Application for employee {0} for date {1} is already present").format(self.employee,self.ot_date))


	def validate_salary_processed_days(self):
		last_processed_pay_slip = frappe.db.sql("""
			select start_date, end_date from `tabSalary Slip`
			where docstatus = 1 and employee = %s
			and (%s between start_date and end_date)
			order by modified desc limit 1
		""",(self.employee, self.ot_date))

		if last_processed_pay_slip:
			frappe.throw(_("Salary already processed for period between {0} and {1}, Overtime date cannot be between this date range.").format(formatdate(last_processed_pay_slip[0][0]),
				formatdate(last_processed_pay_slip[0][1])))

	def validate(self):
		set_employee_name(self)
		self.validate_employee()
		self.validate_duplicate_record()
		self.validate_salary_processed_days()
		


	def validate_employee(self):
		salary_slip_based_on=frappe.db.get_value("Employee", self.employee, "salary_slip_based_on")
		if  salary_slip_based_on!= 'Leave Application':
			frappe.throw(_("Employee {0} , uses {1} based overtime and hence not eligible to use Overtime Application").format(self.employee_name,salary_slip_based_on))


	def on_update(self):
		if self.status == "Open" and self.docstatus < 1:
			# notify overtime approver about creation
			self.notify_leave_approver()
			pass

	def on_submit(self):
		if self.status == "Open":
			frappe.throw(_("Only Overtime Applications with status 'Approved' and 'Rejected' can be submitted"))
		if self.status == "Approved":
			self.validate_salary_processed_days()

		#self.update_attendance()
		#self.create_additional_salary_slip()
		# notify overtime applier about approval
		self.notify_employee()
		self.reload()

	def on_cancel(self):
		self.status = "Cancelled"
		# notify overtime applier about cancellation
		self.notify_employee()
		self.cancel_attendance()
		#self.attendance=None


	def create_additional_salary_slip(self):
			pass
			# 	if self.approved_ot_mins>0:
			# 		per_minute_amount_for_additional_salary_based_on = frappe.db.get_value("Company", company, "per_minute_amount_for_additional_salary_based_on")
			# 		if per_minute_amount_for_additional_salary_based_on=='Fixed Days':
			# 			no_of_fixed_days=frappe.db.get_value("Company", company, "no_of_fixed_days")
			# per_min=total_amt/cint(no_of_fixed_days)/8/60
			# 		ot_factor = frappe.db.get_value("Company", company, "overtime_earning_factor")
			# 		ot_amount=(per_min)*overtime *ot_factor
			# 		print 'overtime_earning'
			# 		ad_sal = frappe.new_doc("Additional Salary")
			# 		ad_sal.employee=self.employee
			# 		ad_sal.salary_component='Overtime'
			# 		ad_sal.amount=d.overtime_earning
			# 		ad_sal.payroll_date=self.posting_date
			# 		ad_sal.overwrite_salary_structure_amount=0
			# 		ad_sal.save()
			# 		ad_sal.submit()

	def update_attendance(self):
		if self.status == "Approved":
			if self.attendance:
				frappe.db.sql("""update `tabAttendance` set overtime = %s\
						where name = %s""",(self.approved_ot_mins, self.attendance))

			# elif getdate(self.to_date) <= getdate(nowdate()):
			# 	for dt in daterange(getdate(self.from_date), getdate(self.to_date)):
			# 		date = dt.strftime("%Y-%m-%d")
			# 		doc = frappe.new_doc("Attendance")
			# 		doc.employee = self.employee
			# 		doc.attendance_date = date
			# 		doc.company = self.company
			# 		doc.leave_type = self.leave_type
			# 		doc.status = "Half Day" if date == self.half_day_date else "On Leave"
			# 		doc.flags.ignore_validate = True
			# 		doc.insert(ignore_permissions=True)
			# 		doc.submit()

	def cancel_attendance(self):
		if self.docstatus == 2:
			if self.attendance:
				frappe.db.sql("""update `tabAttendance` set overtime = %s\
						where name = %s""",('0', self.attendance))		
				

	def notify_employee(self):
		employee = frappe.get_doc("Employee", self.employee)
		if not employee.user_id:
			return

		parent_doc = frappe.get_doc('Overtime Application', self.name)
		args = parent_doc.as_dict()

		template = frappe.db.get_single_value('HR Settings', 'overtime_status_notification_template')
		if not template:
			frappe.msgprint(_("Please set default template for Overtime Status Notification in HR Settings."))
			return
		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)

		self.notify({
			# for post in messages
			"message": message,
			"message_to": employee.user_id,
			# for email
			"subject": email_template.subject,
			"notify": "employee"
		})

	def notify_leave_approver(self):
		if self.overtime_approver:
			parent_doc = frappe.get_doc('Overtime Application', self.name)
			args = parent_doc.as_dict()

			template = frappe.db.get_single_value('HR Settings', 'overtime_approval_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Overtime Approval Notification in HR Settings."))
				return
			email_template = frappe.get_doc("Email Template", template)
			message = frappe.render_template(email_template.response, args)

			self.notify({
				# for post in messages
				"message": message,
				"message_to": self.leave_approver,
				# for email
				"subject": email_template.subject
			})

	def notify(self, args):
		args = frappe._dict(args)
		# args -> message, message_to, subject
		if cint(self.follow_via_email):
			contact = args.message_to
			if not isinstance(contact, list):
				if not args.notify == "employee":
					contact = frappe.get_doc('User', contact).email or contact

			sender      	    = dict()
			sender['email']     = frappe.get_doc('User', frappe.session.user).email
			sender['full_name'] = frappe.utils.get_fullname(sender['email'])

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
