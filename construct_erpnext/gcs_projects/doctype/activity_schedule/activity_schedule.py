import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, date_diff, getdate

from collections import defaultdict, deque


class ActivitySchedule(Document):
	def validate(self):
		self.validate_dates()
		self.compute_duration()

	def validate_dates(self):
		if self.start_date and self.end_date:
			if getdate(self.end_date) < getdate(self.start_date):
				frappe.throw(_("End Date cannot be before Start Date."))

	def compute_duration(self):
		if self.start_date and self.end_date:
			self.duration_days = date_diff(self.end_date, self.start_date) + 1

	def calculate_from_predecessors(self):
		"""Compute start_date and end_date based on predecessor relationships.

		Relationship types:
		  FC (Finish-to-Start): this.start = predecessor.end + delay  (default)
		  CC (Start-to-Start): this.start = predecessor.start + delay
		  FF (Finish-to-Finish): this.end = predecessor.end + delay,
		                         then this.start = this.end - duration
		"""
		if not self.predecessors:
			return

		latest_start = None
		duration = cint(self.duration_days) or 1

		for row in self.predecessors:
			pred = frappe.get_doc("Activity Schedule", row.predecessor_activity)
			delay = cint(row.delay_days)
			rel = row.relationship_type or "FC"

			if rel == "FC":
				candidate_start = add_days(getdate(pred.end_date), delay)
			elif rel == "CC":
				candidate_start = add_days(getdate(pred.start_date), delay)
			elif rel == "FF":
				candidate_end = add_days(getdate(pred.end_date), delay)
				candidate_start = add_days(candidate_end, -(duration - 1))
			else:
				frappe.throw(_("Unknown relationship type '{0}'.").format(rel))
				return

			if latest_start is None or candidate_start > latest_start:
				latest_start = candidate_start

		if latest_start:
			self.start_date = latest_start
			self.end_date = add_days(latest_start, duration - 1)
			self.duration_days = duration


@frappe.whitelist()
def recalculate_project_schedule(project):
	"""Recalculate all Activity Schedules for a project in dependency order.

	Builds a dependency graph, detects circular dependencies, performs
	topological sort, then processes each activity in order.
	"""
	frappe.has_permission("Activity Schedule", ptype="write", throw=True)

	schedules = frappe.get_all(
		"Activity Schedule",
		filters={"project": project},
		fields=["name"],
		order_by="creation asc",
	)

	if not schedules:
		return

	names = {s.name for s in schedules}

	# Build adjacency list and in-degree map for topological sort
	graph = defaultdict(list)
	in_degree = defaultdict(int)

	for name in names:
		in_degree.setdefault(name, 0)

	for s in schedules:
		doc = frappe.get_doc("Activity Schedule", s.name)
		for row in doc.predecessors or []:
			pred = row.predecessor_activity
			if pred not in names:
				continue
			graph[pred].append(s.name)
			in_degree[s.name] += 1

	# Kahn's algorithm for topological sort
	queue = deque([n for n in names if in_degree[n] == 0])
	sorted_order = []

	while queue:
		node = queue.popleft()
		sorted_order.append(node)
		for neighbor in graph[node]:
			in_degree[neighbor] -= 1
			if in_degree[neighbor] == 0:
				queue.append(neighbor)

	if len(sorted_order) != len(names):
		frappe.throw(
			_("Circular dependency detected in Activity Schedule for project {0}.").format(project)
		)

	# Process in topological order
	for name in sorted_order:
		doc = frappe.get_doc("Activity Schedule", name)
		doc.calculate_from_predecessors()
		doc.save()
