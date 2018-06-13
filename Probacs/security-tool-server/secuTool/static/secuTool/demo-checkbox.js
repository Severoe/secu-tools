var groupNumber = 0

function addflag(flag) {
	var id = "#"+flag
	// console.log(id)
	if($(id).hasClass("chosen")) {
		$(id).removeClass("chosen")
	}else {
		$(id).addClass("chosen")
	}
}

function confirmgroup() {
	var buttons = ""
	var flags = ""
	var flag_number = 0
	$('.button-check-box').each(function(){
		// console.log($(this).attr("id"))
		if($(this).hasClass("chosen")) {
			// console.log($(this).parent().text())
			buttons += '<button class="btn btn-light btn-sm" id="'+$(this).attr("id").trim()+"z"+'" onclick="delflag(\''+
			$(this).attr("id").trim()+'\')">'+$(this).parent().text().trim()+'</button>'
			flags += $(this).parent().text().trim()+" "
			$(this).removeClass("chosen")
			flag_number += 1
		}

	})

	if(flag_number === 0) return
	groupNumber += 1
	var form_item = '<input type="hidden" id="'+"input"+groupNumber+'" name="group'+groupNumber+'" value="'+flags+'">'
	var group_item = '<div id="flag-group'+groupNumber+'"> <p>group:</p>'+buttons+
	'<p hidden class = "cnter">'+flag_number+'</p>'+'</div>'
	$('#groups').prepend(group_item)
	$('#group-handin').prepend(form_item)
	
}

function delflag(flag){
	// console.log(flag)
	var button_id = '#'+flag+"z"
	var flag = $(button_id).text().trim()
	var parent_id = $(button_id).parent().attr("id")
	var input_id = '#input'+parent_id.substring(parent_id.length-1,parent_id.length)
	console.log(button_id, input_id)//children(":input").attr("name"))
	//change cnt number
	var cnt = Number($(button_id).parent().children(".cnter").text()) - 1
	console.log(cnt)
	if(cnt === 0) {
		$(button_id).parent().remove()
		$(input_id).remove()
	}else {
		var form_value = $(input_id).attr("value").replace(flag, "")
		console.log(form_value)

		$(button_id).parent().children(".cnter").text(cnt)
		$(input_id).attr({"value":form_value})
		$(button_id).remove()
	}
	
}