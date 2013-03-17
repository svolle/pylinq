$(document).ready(function() {
	var updateResults = function(response, textStatus) {
		if(textStatus === 'success') {
			$('#results').val(JSON.stringify(response));
		} else {
			$('#results').val(JSON.stringify(JSON.parse(response.responseText)));
		}
		
	};
	
	$('#add_player').on('click', function() {
		$.post('/join', { player_name: $('#player_name').val() })
		 .always(updateResults);
	});
	
	$('#start_game').on('click', function() {
		$.post('/start', { player_name: $('#player_name').val() })
		 .always(updateResults);
	});
	
	$('#player_list').on('click', function() {
		$.get('/player_list')
	     .always(updateResults);
	});
	
});