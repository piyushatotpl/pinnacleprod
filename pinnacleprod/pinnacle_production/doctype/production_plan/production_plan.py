import frappe
from datetime import timedelta
from frappe import _


@frappe.whitelist()
def check_feasibility(production_plan):

    plan = frappe.get_doc("Production Plan", production_plan)
    issues = []
    max_lead_time_days = 0
    for pp_item in plan.get("mr_items"):

        item = pp_item.item_code
        lead_time_days = frappe.db.get_value("Item", item, "lead_time_days")

        if lead_time_days > max_lead_time_days:
            max_lead_time_days = lead_time_days
    for po_item in plan.po_items:
        bom = po_item.bom_no

        required_time = frappe.db.get_value("BOM", bom, "custom_required_time")

        total_time = po_item.pending_qty * required_time
        expected_delivery_date = (
            (po_item.planned_start_date + timedelta(minutes=total_time))
            .date()
            .strftime("%d %b %Y")
        )

    production_date = plan.posting_date + timedelta(days=max_lead_time_days)

    formatted_date = production_date.strftime("%d %b %Y")
    frappe.msgprint(
        _(
            "There is a shortage of material. Production can begin on {0} and expected delivery date {1}"
        ).format(formatted_date, expected_delivery_date)
    )
