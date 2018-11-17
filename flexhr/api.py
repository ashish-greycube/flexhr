from __future__ import unicode_literals
import frappe

def set_as_default(self,method):
    if self.is_default:
        frappe.db.sql("update `tabShift Type` set is_default=0 where name != %s",
        self.name)

   