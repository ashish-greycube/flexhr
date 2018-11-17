# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "flexhr"
app_title = "Flex HR"
app_publisher = "GreyCube Technologies"
app_description = "HR customization for saudi arabia"
app_icon = "octicon octicon-organization"
app_color = "#adf442"
app_email = "admin@greycube.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/flexhr/css/flexhr.css"
# app_include_js = "/assets/flexhr/js/flexhr.js"

# include js, css files in header of web template
# web_include_css = "/assets/flexhr/css/flexhr.css"
# web_include_js = "/assets/flexhr/js/flexhr.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "flexhr.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "flexhr.install.before_install"
# after_install = "flexhr.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "flexhr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Shift Type": {
		"on_update": "flexhr.api.set_as_default"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"flexhr.tasks.all"
# 	],
# 	"daily": [
# 		"flexhr.tasks.daily"
# 	],
# 	"hourly": [
# 		"flexhr.tasks.hourly"
# 	],
# 	"weekly": [
# 		"flexhr.tasks.weekly"
# 	]
# 	"monthly": [
# 		"flexhr.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "flexhr.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "flexhr.event.get_events"
# }

