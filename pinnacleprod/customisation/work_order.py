import frappe
from frappe import _
from frappe.utils import date_diff, get_link_to_form
from erpnext.manufacturing.doctype.work_order.work_order import (
    WorkOrder,
    create_job_card,
    CapacityError,
)


class CustomWorkOrder(WorkOrder):
    @frappe.whitelist()
    def validate_sales_order(self):
        if self.sales_order:
            self.check_sales_order_on_hold_or_close()
            so = frappe.db.sql(
                """
                    select so.name, so_item.delivery_date, so.project
                    from `tabSales Order` so
                    inner join `tabSales Order Item` so_item on so_item.parent = so.name
                    left join `tabProduct Bundle Item` pk_item on so_item.item_code = pk_item.parent
                    where so.name=%s and so.docstatus = 1
                        and so.skip_delivery_note  = 0 and (
                        so_item.item_code=%s or
                        pk_item.item_code=%s )
                """,
                (self.sales_order, self.production_item, self.production_item),
                as_dict=1,
            )

            if not so:
                so = frappe.db.sql(
                    """
                        select
                            so.name, so_item.delivery_date, so.project
                        from
                            `tabSales Order` so, `tabSales Order Item` so_item, `tabPacked Item` packed_item
                        where so.name=%s
                            and so.name=so_item.parent
                            and so.name=packed_item.parent
                            and so.skip_delivery_note = 0
                            and so_item.item_code = packed_item.parent_item
                            and so.docstatus = 1 and packed_item.item_code=%s
                    """,
                    (self.sales_order, self.production_item),
                    as_dict=1,
                )

            if len(so):
                if not self.expected_delivery_date:
                    self.expected_delivery_date = so[0].delivery_date

                if so[0].project:
                    self.project = so[0].project

                # if not self.material_request:
                # 	self.validate_work_order_against_so()
            else:
                frappe.throw(_("Sales Order {0} is not valid").format(self.sales_order))

    @frappe.whitelist()
    def prepare_data_for_job_card(self, row, idx, plan_days, enable_capacity_planning):
        self.set_operation_start_end_time(row, idx)

        # Get BOM document
        bom_doc = frappe.get_doc("BOM", self.bom_no)
        print(f"Preparing Job Card for Operation: {row.operation}")

        for op in bom_doc.operations:
            if op.operation == row.operation:
                row.time_in_mins = op.time_in_mins
                row.batch_size = op.batch_size or 1  # Prevent divide-by-zero
                break

        if self.qty and row.time_in_mins:
            print(f"Actual Time in Mins: {row.time_in_mins}")
            total_operation_time = row.time_in_mins
            operation_time_per_unit = total_operation_time / row.batch_size

            row.time_in_mins = operation_time_per_unit * row.job_card_qty

            print(f"Total Qty: {self.qty}")
            print(f"Time in Mins for this Job Card: {row.time_in_mins}")
            print(f"Operation Time Per Unit: {operation_time_per_unit}")
            print(f"Job Card Qty: {row.job_card_qty}")

        # Create Job Card
        job_card_doc = create_job_card(
            self,
            row,
            auto_create=True,
            enable_capacity_planning=enable_capacity_planning,
        )

        # Set scheduled times from Job Card's scheduled time logs
        if enable_capacity_planning and job_card_doc:
            row.planned_start_time = job_card_doc.scheduled_time_logs[-1].from_time
            row.planned_end_time = job_card_doc.scheduled_time_logs[-1].to_time

            if date_diff(row.planned_end_time, self.planned_start_date) > plan_days:
                frappe.message_log.pop()
                frappe.throw(
                    _(
                        "Unable to find the time slot in the next {0} days for the operation {1}. "
                        "Please increase the 'Capacity Planning For (Days)' in the {2}."
                    ).format(
                        plan_days,
                        row.operation,
                        get_link_to_form(
                            "Manufacturing Settings", "Manufacturing Settings"
                        ),
                    ),
                    CapacityError,
                )

        row.db_update()
