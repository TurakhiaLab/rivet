/* Utility functions */

function format_txt(data) {
	var obj = '';
	for (let i = 0; i < data.length; ++i) {
		if (i == data.length - 1) {
			obj += data[i];
			break;
		}
		obj += (data[i] + '\n');
	}
	// Return string obj as array
	return [obj];
}

function get_amino_acid_mutations(
    recomb_node_id, container, y_position, snp_positions, square_dims, num_snps,
    d) {
	var nt_data = [];
	var nt_positions = [];
	fetch('/get_aa_mutations', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({'recomb_node_id': recomb_node_id})
	}).then(res => {
		res.json().then(data => {
			for (nt of data['nt']) {
				nt_data.push(nt);
			}
			for (let i = 0; i < nt_data.length; ++i) {
				nt_positions.push(nt_data[i].slice(1, -1));
			}
			add_aa_labels(
			    container, y_position - 40, snp_positions,
			    square_dims, num_snps, d, nt_positions, data['aa']);

			d3.selectAll('.bases').style('opacity', '0.2');
		});
	});
	return nt_data;
}

function usher_button_info_hide(tooltip) {
	tooltip.html(``).style('visibility', 'hidden');
}

function usher_button_info_display(tooltip) {
	var value = ' ';
	var name = ' : ';
	tooltip.html(`${name}: ${value}`)
	    .style('visibility', 'visible')
	    .style(
		'right',
		'50' +
		    'px')
	    .style(
		'top',
		'100' +
		    'px');
}

function view_usher_tree(d) {
	let tree_selected = 'public';
	let full_table_select = document.getElementById('full_table');
	// Check if public or full table is selected
	if (!full_table_select.hidden) {
		tree_selected = 'full';
	}

	fetch('/get_usher_link', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify(
		    {node: d['NODE_IDS']['Recomb'], tree: tree_selected})
	}).then(res => {
		res.json().then(data => {
			// Open usher.bio link in new tab
			window.open(data['url'], '_blank');
		});
	});
}

function get_detailed_overview(overview, d) {
	// Get additional data from table for each of these fields
	fetch('/get_overview', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({'id': d['ID']})
	}).then(res => {
		res.json().then(data => {
			document.getElementById('off_canvas_right_body')
			    .textContent = '';

			const detailed_overview =
			    document.getElementById('off_canvas_right_body');

			append_text(
			    detailed_overview,
			    'Recombinant Node ID: ' + d['NODE_IDS']['Recomb']);
			append_text(
			    detailed_overview,
			    'Current Recombinant Lineage Designation: ' +
				data['overview']['recomb_lineage']);
			append_text(
			    detailed_overview,
			    'Recombinant Origin Date: ' +
				data['overview']['recomb_date']);

			append_text(
			    detailed_overview,
			    'Recombinant Between: ' +
				data['overview']['donor_lineage'] + ' and ' +
				data['overview']['acceptor_lineage']);

			append_text(
			    detailed_overview,
			    'Number Sequences: ' +
				data['overview']['num_desc'].toLocaleString());

			append_text(
			    detailed_overview,
			    'Earliest Sequence: ' +
				data['overview']['earliest_seq']);

			append_text(
			    detailed_overview,
			    'Most Recent Sequence: ' +
				data['overview']['latest_seq']);

			append_text(
			    detailed_overview,
			    'Countries Detected: ' +
				data['overview']['countries']);

			append_text(detailed_overview, 'QC Flags: ');
			append_list(
			    detailed_overview, data['overview']['qc_flags']);
			// TODO: Add
			// append_text(overview,
			// 'Defining
			// Mutations:
			// ');
		});
	});
}

function select_analysis_plot(selected_tree) {
	let histogram_selections =
	    document.getElementById('histogram_selections');
	let histogram_visuals = document.getElementById('histogram_visuals');
	if (selected_tree == 'public') {
		$('#full_tree_analysis').removeClass('active');
		$('#public_tree_analysis').addClass('active');
		if (histogram_selections.hidden) {
		}
	} else {
		$('#public_tree_analysis').removeClass('active');
		$('#full_tree_analysis').addClass('active');
	}
}

function render_table(selected_tree) {
	let full_table_select = document.getElementById('full_table');
	let public_table_select = document.getElementById('table_container');
	if (selected_tree == 'public') {
		$('#full_tree').removeClass('active');
		$('#public_tree').addClass('active');
		full_table_select.hidden = true;

		if (public_table_select.hidden) {
			public_table_select.removeAttribute('hidden');
			$('#datatable').show();
			$('#datatable').DataTable().columns.adjust();
		}
	} else {
		$('#public_tree').removeClass('active');
		$('#full_tree').addClass('active');
		public_table_select.hidden = true;
		full_table_select.removeAttribute('hidden');
		$('#full_datatable').show();
		$('#full_datatable').DataTable().columns.adjust();
	}
}

function next_result(id) {
	// Get current result table page length
	var pageLength = ($('#datatable').DataTable().page() + 1) *
	    $('#datatable').DataTable().page.len();

	fetch('/get_data', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({'row_id': id, 'click': 'next'})
	}).then(res => {
		res.json().then(data => {
			track(data);
			var row = data['ID'];
			$(document).ready(function() {
				var table = $('#datatable').DataTable();
				var row_idx = parseInt(row) - 1;
				var next_idx = parseInt(row);

				if ($('#datatable tbody tr')
					.hasClass('selected')) {
					if (next_idx == pageLength) {
						// Move to next page
						$('#datatable')
						    .DataTable()
						    .page('next')
						    .draw(false);
					}
					// Remove previously selected
					$('#datatable tbody tr')
					    .removeClass('selected');
				}
				$($('#datatable')
				      .DataTable()
				      .row(next_idx)
				      .node())
				    .addClass('selected');
			});
		});
	});
}

function previous_result(id) {
	// Get current result table page length
	var pageLength = ($('#datatable').DataTable().page() + 1) *
	    $('#datatable').DataTable().page.len();

	fetch('/get_data', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({'row_id': id, 'click': 'previous'})
	}).then(res => {
		res.json().then(data => {
			track(data);
			var row = data['ID'];
			$(document).ready(function() {
				var table = $('#datatable').DataTable();
				var current_idx = parseInt(row) + 1;
				var prev_idx = parseInt(row);

				if (prev_idx ==
				    ((pageLength - 1) -
				     $('#datatable').DataTable().page.len())) {
					// Move to next page
					$('#datatable')
					    .DataTable()
					    .page('previous')
					    .draw(false);
				}
				if ($('#datatable tbody tr')
					.hasClass('selected')) {
					// Remove previously selected row
					$('#datatable tbody tr')
					    .removeClass('selected');
				}
				$($('#datatable')
				      .DataTable()
				      .row(prev_idx)
				      .node())
				    .addClass('selected');
			});
		});
	});
}

function append_text(div, text) {
	let tag = document.createElement('p');
	tag.setAttribute('id', 'overview_text');
	tag.appendChild(document.createTextNode(text));
	div.appendChild(tag);
}

function append_list(div, list) {
	let tag = document.createElement('ul');
	tag.setAttribute('id', 'overview_text');
	list.forEach((element) => {
		let li = document.createElement('li');
		li.setAttribute('class', 'item');
		tag.appendChild(li);
		li.innerHTML = li.innerHTML + element;
	});
	div.appendChild(tag);
	// Add linebreak after last element for Taxonium button
	linebreak = document.createElement('br');
	linebreak.style.lineHeight = '5';
	div.appendChild(linebreak);
}

function init_env(buttons) {
	fetch('/init', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({init: 'init'})
	}).then(res => {
		res.json().then(data => {
			if (data['env'].toLowerCase() == 'local') {
				buttons.forEach((item) => {
					item.setAttribute('hidden', true);
				});
			}
		});
	});
}

function create_button(id, name, pos_left, pos_top, hidden = false) {
	let button = document.createElement('button');
	button.innerHTML = name;
	button.setAttribute('id', id);
	button.type = 'button';
	button.name = 'formBtn';
	button.className = 'btn btn-outline-primary'
	button.style.position = 'absolute';
	button.style.left = pos_left;
	button.style.top = pos_top;
	document.body.appendChild(button);
	return button;
}

function download_snv_plot(inner_svg, node_name) {
	if (inner_svg) {
		var copied_svg = inner_svg.cloneNode(true);
		document.body.appendChild(copied_svg);
		const g = copied_svg.querySelector('g')
		// Adjust for genomic
		// coordinate track axis offset
		g.setAttribute('transform', 'translate(0,600)')
		// Add extra space on end for rotated
		// column position labels
		copied_svg.setAttribute(
		    'width', copied_svg.getBBox().width + 20)
		copied_svg.setAttribute(
		    'height', copied_svg.getBBox().height + 200)
		var svgAsXML =
		    (new XMLSerializer).serializeToString(copied_svg);
		var svgData =
		    `data:image/svg+xml,${encodeURIComponent(svgAsXML)}`
		var link = document.createElement('a');
		document.body.appendChild(link);
		link.setAttribute('href', svgData);
		link.setAttribute('download', node_name + '_trio.svg');
		link.click();
		document.body.removeChild(copied_svg);
		URL.revokeObjectURL(link.href);
		document.body.removeChild(link);
		link.remove();
	}
}

function serialize_object(file_name, obj) {
	// Create download file
	const file = new File(obj, file_name);

	const link = document.createElement('a');
	link.style.display = 'none';
	link.href = URL.createObjectURL(file);
	link.download = file.name;

	document.body.appendChild(link);
	link.click();

	setTimeout(() => {
		URL.revokeObjectURL(link.href);
		link.parentNode.removeChild(link);
	}, 0);
}

function format_descedants(data) {
	var string = '';
	for (const element of data) {
		string += element;
		string += '<br>';
	}
	string += '<br>'
	return string;
}

function format_tsv(data) {
	var obj = '';
	for (let i = 0; i < data.length; ++i) {
		for (let j = 0; j < data[i].length; ++j) {
			if (j == data[i].length - 1) {
				obj += data[i][j];
				obj += '\n';
			} else {
				obj += data[i][j];
				obj += '\t';
			}
		}
	}
	// Return string obj as array
	return [obj];
}

function download_all_descendants(tree_type) {
	fetch('/get_all_descendants', {
		method: 'POST',
		headers: {'Content-Type': 'text/plain'},
		body: {download: 'all_descendants'}
	}).then(res => {});
	return '/get_all_descendants';
}

function download_table(tree_type) {
	fetch('/download_table', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({'tree_type': tree_type})
	}).then(res => {
		res.json().then(data => {
			var file_name = 'recombination_results.txt';
			formatted_data = format_tsv(data);
			serialize_object(file_name, formatted_data);
		});
	});
}

function display_descendants(label_node_id) {
	if (label_node_id == 'None') {
		return;
	}
	let tree_selected = 'public';
	let full_table_select = document.getElementById('full_table');
	// Check if public or full table is selected
	if (!full_table_select.hidden) {
		tree_selected = 'full';
	}

	fetch('/get_descendants', {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({node: label_node_id, tree: tree_selected})
	}).then(res => {
		res.json().then(data => {
			// Remove query descendants functionality for
			// local server
			if (!data) {
				return;
			}
			// First remove previously fetched list
			// of descendants
			d3.select('#desc').remove();

			// Toggle offcanvas left
			var myOffcanvas =
			    document.getElementById('off_canvas_left')
			var bsOffcanvas = new bootstrap.Offcanvas(myOffcanvas)
			bsOffcanvas.show()

			// Get descendants data and format 1 per
			// line
			var desc_string = format_descedants(data);

			var num_des = data.length;
			// Set text formatting size
			var font_size = 14;

			var selection = d3.select('#off_canvas_left_body')
					    .append('p')
					    .attr('id', 'desc');

			const paragraph = d3.select('#desc');
			paragraph.append('foreignObject')
			    .append('xhtml:p')
			    .attr('font-size', font_size)
			    .html(desc_string);

			const desc_button =
			    document.querySelector('#download_descendants');
			if (desc_button) {
				desc_button.addEventListener('click', () => {
					window.location.href =
					    '/download_select_descendants?id=' +
					    label_node_id;
				}, false);
			}
		});
	});
}

function download_taxonium() {
	fetch('/download_taxonium', {
		method: 'POST',
	}).then(res => {
		res.json().then(data => {
			// Format: year-month-date
			var date = data['date'];
			//  NOTE: storage bucket public_trees is
			//  hardcoded
			var url =
			    'https://storage.googleapis.com/public_trees/' +
			    date + '.taxonium.jsonl.gz'
			window.location.href = url;
		});
	});
}

function download_tree() {
	fetch('/download_mat', {
		method: 'POST',
	}).then(res => {
		res.json().then(data => {
			// Format: year-month-date
			var date = data['date'];
			// Format:
			// "public-year-month-date.all.masked.pb.gz"
			var mat = 'public-' + date +
			    '.all.masked.nextclade.pangolin.pb.gz'
			date = date.split('-').join('/');
			date = date + '/' + mat;
			//  Format:
			//  'http://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/year/month/date/';
			var mat_url =
			    'https://hgdownload.soe.ucsc.edu/goldenPath/wuhCor1/UShER_SARS-CoV-2/' +
			    date;
			window.location.href = mat_url;
		});
	});
}

function determine_informative(match, colors) {
	// Matches the acceptor
	if (match == 'A') {
		return colors['recomb_match_acceptor'];
	} else {
		// Matches the donor
		return colors['recomb_match_donor'];
	}
}

function display_legend(svg, colors) {
	var items = [
		'Recombinant matches acceptor', 'Recombinant matches donor',
		'Non-Recombinant-Informative'
	];
	//'Breakpoint Intervals'

	var color_range = [
		colors['recomb_match_acceptor'], colors['recomb_match_donor'],
		colors['non_informative_site']
	];
	var legend_square_size = 30;
	var num_items = 3;

	const legend_item_starting_height = 450;
	var legend_item_h = legend_item_starting_height;

	// Add legend row color square
	svg.selectAll('squares')
	    .data(color_range)
	    .enter()
	    .append('rect')
	    .attr('x', 10)
	    .attr(
		'y',
		function(d, i) {
			if (i == 0) {
				return legend_item_starting_height;
			}
			return legend_item_h += legend_square_size + 5;
		})
	    .attr('width', legend_square_size)
	    .attr('height', legend_square_size)
	    .attr('fill', d => d);

	// Reset item height to starting height
	legend_item_h = legend_item_starting_height;

	// Add legend row label
	svg.selectAll('labels')
	    .data(items)
	    .enter()
	    .append('text')
	    .attr('x', 45)
	    .attr(
		'y',
		function(d, i) {
			if (i == 0) {
				return legend_item_starting_height +
				    (legend_square_size / 2);
			}
			legend_item_h += legend_square_size + 5;
			return legend_item_h + (legend_square_size / 2);
		})
	    .attr(
		'fill',
		function(d, i) {
			return color_range[i];
		})
	    .text(d => d)
	    .attr('text-anchor', 'left')
	    .style('alignment-baseline', 'middle');
}
