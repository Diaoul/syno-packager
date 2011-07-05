$(document).ready(function() {
	$('#tasks').dataTable({
		"bAutoWidth": true,
		"bDeferRender": false,
		"bFilter": false,
		"bInfo": false,
		"bJQueryUI": false,
		"bPaginate": false,
		"bLengthChange": false,
		"bProcessing": false,
		"bScrollInfinite": false,
		"bSort": true,
		"bSortClasses": false,
		"bStateSave": true,
		"oLanguage": {"sEmptyTable": "No process added yet. Add some!"},
		"aoColumns": [null, null, null, null, null, null, null, null, {"bSortable": false}]
	});
});
