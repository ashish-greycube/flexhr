from __future__ import unicode_literals
import frappe
from frappe.desk.page.setup_wizard.setup_wizard import make_records

def install_fixtures():
    records = [
 {
  "docstatus": 0,
  "doctype": "Email Template",
  "name": "Auto Attendance Nightly Job Notification",
  "response": "<h3>Dear System Manager,</h3><div><br></div><h3>Details:</h3><table class=\"table table-bordered\"><tbody><tr><td data-row=\"1\">Run On</td><td data-row=\"1\">{{run_on}}</td></tr><tr><td data-row=\"2\">Run Status</td><td data-row=\"2\">{{run_status}}</td></tr><tr><td data-row=\"row-o4rq\">Total Review Required Count</td><td data-row=\"row-o4rq\">{{review_count}} </td></tr><tr><td data-row=\"insert-row-above\">HR Review Required Count</td><td data-row=\"insert-row-above\">{{hr_review_count}}</td></tr><tr><td data-row=\"4\">Admin Review Required Count</td><td data-row=\"4\">{{admin_review_count}}</td></tr><tr><td data-row=\"insert-row-below\">Attendance Processed From Date</td><td data-row=\"insert-row-below\">{{from_date}}</td></tr><tr><td data-row=\"row-vrth\">Attendance Processed To Date</td><td data-row=\"row-vrth\">{{to_date}}</td></tr><tr><td data-row=\"row-mjpj\">Attendance Log URL</td><td data-row=\"row-mjpj\">{{att_log_url}}</td></tr></tbody></table><h3>Error: {{error}}</h3><div><br></div>",
  "subject": "[Important] [FlexHR] Auto Attendance System",
  "owner": "Administrator"
 },
 {
  "docstatus": 0,
  "doctype": "Email Template",
  "name": "Overtime Approval Notification",
  "response": "<h1>Overtime Approval Notification</h1><h3>Details:</h3><table class=\"table table-bordered\"><tbody><tr><td data-row=\"1\">Employee</td><td data-row=\"1\">{{employee_name}}</td></tr><tr><td data-row=\"2\">Overtime Date</td><td data-row=\"2\">{{ot_date}}</td></tr><tr><td data-row=\"3\">Applicable Overtime (in mins)</td><td data-row=\"3\">{{applicable_ot_mins}}</td></tr><tr><td data-row=\"4\">Approved Overtime (in mins)</td><td data-row=\"4\">{{approved_ot_mins}}</td></tr><tr><td data-row=\"5\">Status</td><td data-row=\"5\">{{status}}</td></tr></tbody></table>",
  "subject": "Overtime Approval Notification",
  "owner": "Administrator"
 },
 {
  "docstatus": 0,
  "doctype": "Email Template",
  "name": "Overtime Status Notification",
  "response": "<h1>Overtime Application Notification</h1><h3>Details:</h3><table class=\"table table-bordered\"><tbody><tr><td data-row=\"1\">Employee</td><td data-row=\"1\">{{employee_name}}</td></tr><tr><td data-row=\"2\">Overtime Date</td><td data-row=\"2\">{{ot_date}}</td></tr><tr><td data-row=\"4\">Approved Overtime (in mins)</td><td data-row=\"4\">{{approved_ot_mins}}</td></tr><tr><td data-row=\"5\">Status</td><td data-row=\"5\">{{status}}</td></tr></tbody></table><div><br></div>",
  "subject": "Overtime Status Notification",
  "owner": "Administrator"
 },
 {
  "docstatus": 0,
  "doctype": "Email Template",
  "name": "Attendance Reconciliation Information",
  "response": "<h1>Attendance Reconciliation Information</h1><h3>Details:</h3><table class=\"table table-bordered\"><tbody><tr><td data-row=\"1\">Employee</td><td data-row=\"1\">{{employee_name}}</td></tr><tr><td data-row=\"2\">Attendance Date</td><td data-row=\"2\">{{attendance_date}}</td></tr><tr><td data-row=\"row-aqp8\">Attendance Status</td><td data-row=\"row-aqp8\">{{present_status}} , presence</td></tr><tr><td data-row=\"insert-row-above\">Checkin Time as per device</td><td data-row=\"insert-row-above\">{{checkin_time}}</td></tr><tr><td data-row=\"4\">Checkout Time as per device</td><td data-row=\"4\">{{checkout_time}}</td></tr><tr><td data-row=\"5\">Leave Application</td><td data-row=\"5\"><span style=\"background-color: rgb(255, 255, 255); color: rgb(54, 65, 76);\">{{ leave_url }}</span></td></tr></tbody></table><h3>Remark:</h3><div>Based on above data, you may approach your Leave Approver/HR to get your leave for {{attendance_date}} cancelled so as to avail 'Present' Attendance.</div>",
  "subject": "Attendance Reconciliation Information",
  "owner": "Administrator"
 },
 {
  "docstatus": 0,
  "doctype": "Email Template",
  "name": "Attendance Reconciliation Request",
  "response": "<h1>Attendance Reconciliation Request</h1><h3>Details:</h3><table class=\"table table-bordered\"><tbody><tr><td data-row=\"1\">Employee</td><td data-row=\"1\">{{employee_name}}</td></tr><tr><td data-row=\"2\">Attendance Date</td><td data-row=\"2\">{{attendance_date}}</td></tr><tr><td data-row=\"row-o4rq\">Attendance Status</td><td data-row=\"row-o4rq\">{{present_status}} , presence</td></tr><tr><td data-row=\"insert-row-above\">Checkin Time as per device</td><td data-row=\"insert-row-above\">{{checkin_time}}</td></tr><tr><td data-row=\"4\">Checkout Time as per device</td><td data-row=\"4\">{{checkout_time}}</td></tr><tr><td data-row=\"5\">Leave Application</td><td data-row=\"5\"><span style=\"background-color: rgb(255, 255, 255); color: rgb(54, 65, 76);\">{{ leave_url }}</span></td></tr></tbody></table><h3>Remark:</h3><ol><li data-list=\"ordered\">{{attendance_request_remark}}</li></ol>",
  "subject": "Attendance Reconciliation Request",
  "owner": "Administrator"
 }
]
    
    make_records(records)        