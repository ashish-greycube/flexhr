from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import date_diff, add_days, getdate
from erpnext.hr.doctype.employee.employee import is_holiday

def set_as_default(self,method):
    if self.is_default:
        frappe.db.sql("update `tabShift Type` set is_default=0 where name != %s",
        self.name)


def validate_if_attendance_not_applicable(self,method):
        request_days = date_diff(self.to_date, self.from_date) + 1
        for number in range(request_days):
                attendance_date = add_days(self.from_date, number)
                skip_attendance = validate_if_holiday_or_leave(self,attendance_date)


def copy_fields_to_attendance(self,method):
        frappe.db.sql("""update `tabAttendance` set  
        checkin_time=%s,
        checkout_time=%s,
        duration=%s,
        shift_in_time=%s,
        shift_out_time=%s,
        shift_type=%s,
        early=%s,
        delay=%s,
        overtime=%s,
        review_remark='AR was system generated'
        where attendance_request = %s""",
        (self.checkin_time,
	self.checkout_time,
	self.duration,
	self.shift_in_time,
	self.shift_out_time,
	self.shift_type,
	self.early,
	self.delay,
	self.overtime,
        self.name))

def validate_if_holiday_or_leave(self,attendance_date) :
        # Check if attendance_date is a Holiday
        if is_holiday(self.employee, attendance_date):
                frappe.throw(_("Attendance not submitted for {0} as it is a Holiday.").format(attendance_date))
                return False

        # Check if employee on Leave
        leave_record = frappe.db.sql("""select half_day from `tabLeave Application`
                where employee = %s and %s between from_date and to_date
                and docstatus = 1""", (self.employee, attendance_date), as_dict=True)
        print 'leave_record'
        print leave_record
        if leave_record:
                frappe.throw(_("Attendance not submitted for {0} as {1} on leave.").format(attendance_date, self.employee))
                return False
         # There is no use allowing half day attendance, instead employee should go for half day leave if not done
        if self.half_day==1:
                frappe.throw(_("Attendance not submitted for half day. Instead put half day leave on {0}").format(attendance_date))
                return False
        return True