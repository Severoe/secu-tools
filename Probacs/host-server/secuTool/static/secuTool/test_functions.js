var groupNumber = 0
var interval = 1000;
var finished_status = false
var text = ""

function addflag(flag) {
    var id = "#" + flag
    if ($(id).hasClass("chosen")) {
        $(id).removeClass("chosen")
    } else {
        $(id).addClass("chosen")
    }
}

function delflag(flag) {
    var button_id = '#' + flag + "z"
    var flag = $(button_id).text().trim()
    var parent_id = $(button_id).parent().attr("id")
    var input_id = '#input' + parent_id.substring(parent_id.length - 1, parent_id.length)
    var cnt = Number($(button_id).parent().children(".cnter").text()) - 1
    if (cnt === 0) {
        $(button_id).parent().remove()
        $(input_id).remove()
    } else {
        var form_value = $(input_id).attr("value").replace(flag, "")
        $(button_id).parent().children(".cnter").text(cnt)
        $(input_id).attr({ "value": form_value })
        $(button_id).remove()
    }
}

function selectall() {
    $('.row-button').each(function () {
        if(!$(this).is(":disabled")) {
            $(this).addClass('chosen')
        }
    })
}

function deselectall() {
    $('.row-button').each(function () {
        if(!$(this).is(":disabled")) {
            $(this).removeClass('chosen')
        }
    })
}
function setCurrentJob(job_id){
	// event_id = setInterval(trace_job, interval);
	$('#ongoing-task').text(job_id)
	finished_status = false
}

// invoked when job tracking request has been called
function trace_job() {
	var job_id = $('#ongoing-task').text().trim()
    var finished,total;
	console.log("job: "+job_id)
	if(job_id === "" || job_id === 'None' || finished_status) {
		return
	}
    $.ajax({
        url: "/trace_task",
        dataType : "json",
        data: {
        	task_id: job_id,
        },
        success:  function(response) {
        	console.log(response)
            form_status_report(response)        	
        }
    });
    return
}
function form_status_report(response){
    finished = response.finished
    total = response.total
    if(finished === total) {
        finished_status = true
        // $('#download_wrapper').css('display','block')
        // clearInterval(event_id)
    }
    percent = finished*100/total
    report = "<span id='task_finished'>"+ finished.toString()+"</span> / "+"<span id='task_total'>"+total.toString()+"</span>"+" compilation finished for job id: "+response.task_id
    $('#result-trace').css('display','block')
    $('#result-report').empty()
    $('#result-report').append(report)
    $('#bar-growth').width(percent.toString()+'%')
    // adjost log output
    $('#log-report').empty()
    for(var i in response.log_report) {
        // var d = new Date();
        var log = response.log_report[i]
        var out_theme = ""
        var err_theme = ""
        console.log(log)
        if(log.err === null) {
            log.err = "-"
        }
        if(log.err !== "-") {
            out_theme = "text-align:left;"
        }
        if(log.err !== "-") {
            err_theme = "text-align:left;"
        }
        var log_row = "<tr>"+
            "<td class='report-row' style='column-width: auto;'>"+log.exename.trim()+"</td>"+
            "<td class='report-row' style='column-width: auto;"+out_theme+"'>"+log.status+"</td>"+
            "<td class='report-row' style='column-width: auto;"+err_theme+"'>"+log.err+"</td>"+
            // "<td>" + d.year + d.month + d.day + d.hours + d.minutes + d.seconds + "</td>"
            "</tr>"
        $("#log-report").append(log_row)
    }
    $('#trace-wrapper').css("display","block");
}



function getOS() {
    var json_profiles = $('#json_profiles').text()
    if (json_profiles === "" || json_profiles === null) return
    text = JSON.parse(json_profiles)
    var os_list = []
    for (os in text) {
        os_list.push(os)
    }
    os_list.sort()
    var options = ""
    for (os in os_list) {
        options += "<option>" + os_list[os] + "</option>"
    }
    $('#target_os').append(options)
}

function getCompiler(os) {
    $('#compiler').empty()
    $('#os_selected').text(os)
    var compiler_list = []
    for (compiler in text[os]) {
        compiler_list.push(compiler)
    }
    compiler_list.sort()
    var options = "<option value='' disabled selected>Select</option>"
    for (compiler in compiler_list) {
        options += "<option>" + compiler_list[compiler] + "</option>"
    }
    $('#compiler').append(options)
}

function getProfiles(compiler) {
    $('#profiles').empty()
    $('#compiler_selected').text(compiler)
    var os = $('#os_selected').text()
    var plist = text[os][compiler].sort()
    var options = ""
    var boxes = ""
    for (p in plist) {
        options += "<input type='checkbox' onchange='peek(this.id);' name='profile' id='" + plist[p] +
                    "' value='" + plist[p] + "'/>" + plist[p] + "<br/>"
        boxes += "<div id='" + plist[p] + "_box'></div>"
    }
    $('#profile_content').append(boxes)
    $('#profiles').append(options)
}

function peek(profile) {
    if (document.getElementById(profile).checked === true) {
        $.ajax({
            type: 'POST',
            url: "/peek_profile",
            dataType: "json",
            data: {
                target_os: $('#os_selected').text(),
                compiler: $('#compiler_selected').text(),
                name: profile,
            },
            success: function (response) {
                if ('message' in response) {
                    message += response['message']
                    alert(message)
                } else {
                    var id = '#' + profile + '_box'
                    var message = ""
                    message += "<div class='peek_text'> name: &nbsp &nbsp &nbsp &nbsp" + response['name'] + "<br>"
                    message += "target_os: &nbsp" + response['target_os'] + "<br>"
                    message += "compiler: &nbsp &nbsp" + response['compiler'] + "<br>"
                    message += "version: &nbsp &nbsp &nbsp" + response['version'] +  "<br>"
                    message += "flag: &nbsp &nbsp &nbsp" + response['flag'] + "<br>"
                    message += "uploader: &nbsp &nbsp" + response['uploader'] + "<br>"
                    message += "upload_time: &nbsp" + response['upload_time'] + "<br></div><br>"
                    $(id).append(message)
                }
            }
        });
    } else {
        var id = '#' + profile + '_box'
        $(id).empty()
    }
}

// when hit download, append chosen field into form, then trigger form handin
function download_search() {
    cnt = 0
    $('.row-button').each(function () {
        if($(this).hasClass('chosen')){
            if($(this).closest('tr').find('td.download_status').text().trim() === "success") {
                cnt += 1
                var task_id = $(this).closest('tr').find('td.download_id').text().trim()
                var exename = $(this).closest('tr').find('td.download_exe').text().trim()
                var rcd = "<input name='exe_pair' value="+task_id+"$%$"+exename+">"
                $('#search_dld').prepend(rcd)
            }
        }
    })
    if(cnt !== 0) {
        $('#search_dld').submit()
    }
}


function terminate(){
    var finished = $('#task_finished').text().trim()
    var total = $('#task_total').text().trim()
    if(finished === total || finished_status) { //if already finished, we canot terminate
        return
    }
    var job_id = $('#ongoing-task').text().trim()
    var finished = 
    $.ajax({
        type: 'POST',
        url: "/terminate",
        dataType: "json",
        data: {
            task_id: job_id,
        },
        success: function (response) {
            console.log(response)
            form_status_report(response)  
        }
    });
}

function onload_wrapper() {
    calendar()
    getOS()
    trace_job()

}

window.onload = onload_wrapper;
var event_id = window.setInterval(trace_job, interval);

//**************** function for tar downloading
function download_tar(){
    var id = $('#ongoing-task').text().trim()
    var finished = $('#task_finished').text().trim()
    var total = $('#task_total').text().trim()
    if(finished !== total) return;
    console.log("eligible for download")
    $('input[name="downloadtaskid"]').val(id)
    console.log($('input[name="downloadtaskid"]').val())
    $('#download_full').submit()
}

function calendar(){ 
      $( "#dateafter" ).datepicker();
      $( "#datebefore" ).datepicker();  
}