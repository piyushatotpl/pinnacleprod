frappe.pages["bom-comparison-tool-1"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "BOM Comparison Tool",
		single_column: true,
	});

	// Layout container
	$(
		`<div class="bom-filters-section" style="padding: 20px 0;">
			<div id="filter_area"></div>
			<div style="margin-top: 20px;">
				<button class="btn btn-primary" id="run_comparison">Compare BOMs</button>
			</div>
		</div>
		<hr />
		<div id="comparison_results" class="results-area" style="padding-top: 20px;"></div>`
	).appendTo(page.body);

	// Create filters using FieldGroup
	const field_group = new frappe.ui.FieldGroup({
		fields: [
			{
				fieldname: "sales_order",
				label: "Sales Order",
				fieldtype: "Link",
				options: "Sales Order",
				reqd: 1,
			},
			{
				fieldname: "production_item",
				label: "Production Item",
				fieldtype: "Link",
				options: "Item",
				reqd: 1,
			},
			{
				fieldname: "qty",
				label: "Quantity",
				fieldtype: "Float",
				reqd: 1,
			},
			{
				fieldname: "planned_start_time",
				label: "Planned Start Time",
				fieldtype: "Datetime",
				reqd: 1,
				default: frappe.datetime.now_datetime(),
			},
			{
				fieldname: "bom_1",
				label: "Select BOM 1",
				fieldtype: "Link",
				options: "BOM",
				reqd: 1,
			},
			{
				fieldname: "bom_2",
				label: "Select BOM 2",
				fieldtype: "Link",
				options: "BOM",
				reqd: 1,
			},
		],
		parent: $("#filter_area"),
	});
	field_group.make();

	// Auto-fill item/qty from SO
	field_group.get_field("sales_order").df.onchange = function () {
		const so = field_group.get_value("sales_order");
		if (so) {
			frappe.db.get_doc("Sales Order", so).then((doc) => {
				if (doc.items?.length > 0) {
					const first_item = doc.items[0];
					field_group.set_value("production_item", first_item.item_code);
					field_group.set_value("qty", flt(first_item.qty));
				}
			});
		}
	};

	// Filter BOMs for selected item
	field_group.get_field("production_item").df.onchange = function () {
		const item_code = field_group.get_value("production_item");
		if (item_code) {
			["bom_1", "bom_2"].forEach((bom_fieldname) => {
				field_group.get_field(bom_fieldname).get_query = function () {
					return {
						filters: {
							item: item_code,
							is_active: 1,
						},
					};
				};
			});
		}
	};

	// Compare button logic
	$("#run_comparison").on("click", function () {
		const args = {
			item_code: field_group.get_value("production_item"),
			qty: field_group.get_value("qty"),
			planned_start_time: field_group.get_value("planned_start_time"),
			boms: [field_group.get_value("bom_1"), field_group.get_value("bom_2")],
		};

		if (
			!args.item_code ||
			!args.qty ||
			!args.planned_start_time ||
			!args.boms[0] ||
			!args.boms[1]
		) {
			frappe.msgprint("Please fill all fields and select two BOMs.");
			return;
		}

		frappe.call({
			method: "pinnacleprod.pinnacle_production.page.bom_comparison_tool_1.bom_comparison_tool_1.get_selected_bom_comparison",
			args,
			freeze: true,
			freeze_message: "Analyzing BOMs...",
			callback: function (r) {
				if (r.message) {
					render_selected_comparison(r.message);
				} else {
					frappe.msgprint("No data returned from server.");
				}
			},
			error: function () {
				frappe.msgprint("Server error while fetching BOM comparison.");
			},
		});
	});
};

function render_selected_comparison(data) {
	const results_area = $("#comparison_results");
	results_area.empty();

	if (data.length !== 2) {
		results_area.html(
			`<div class="alert alert-warning">Two BOMs must be selected for comparison.</div>`
		);
		return;
	}

	const [bom1, bom2] = data;

	const table = `
		<table class="table table-bordered">
			<thead>
				<tr>
					<th>Field</th>
					<th>${bom1.bom_name}</th>
					<th>${bom2.bom_name}</th>
				</tr>
			</thead>
			<tbody>
				<tr><td>Workstation</td><td>${bom1.workstation_name}</td><td>${bom2.workstation_name}</td></tr>
				<tr><td>Availability</td><td>${bom1.availability}</td><td>${bom2.availability}</td></tr>
				<tr><td>Material Cost</td><td>${frappe.format(bom1.material_cost, {
					fieldtype: "Currency",
				})}</td><td>${frappe.format(bom2.material_cost, {
		fieldtype: "Currency",
	})}</td></tr>
				<tr><td>Operating Cost</td><td>${frappe.format(bom1.operating_cost, {
					fieldtype: "Currency",
				})}</td><td>${frappe.format(bom2.operating_cost, {
		fieldtype: "Currency",
	})}</td></tr>
				<tr><td>Total Cost</td><td><b>${frappe.format(bom1.total_cost, {
					fieldtype: "Currency",
				})}</b></td><td><b>${frappe.format(bom2.total_cost, {
		fieldtype: "Currency",
	})}</b></td></tr>
				<tr><td>Scrap Cost</td><td>${frappe.format(bom1.scrap_cost, {
					fieldtype: "Currency",
				})}</td><td>${frappe.format(bom2.scrap_cost, { fieldtype: "Currency" })}</td></tr>
				<tr><td>Scrap %</td><td>${bom1.scrap_percentage}%</td><td>${bom2.scrap_percentage}%</td></tr>
			</tbody>
		</table>`;

	results_area.html(table);
}
