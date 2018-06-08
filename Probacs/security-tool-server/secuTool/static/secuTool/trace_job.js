var interval = 1000;

//send request to check job process
function tracejob() {
	var job_id = $('#task_id').text()
    var percent,report;
	// console.log("job: "+job_id)
	if(job_id === "" ) {
		return
	}
    $.ajax({
        url: "/trace",
        dataType : "json",
        data: {
        	task_id: job_id,
        },
        success:  function(response) {
        	console.log(response)
        	percent = response.finished*100/response.total
        	report = (response.finished).toString()+" / "+(response.total).toString()+" compilation finished for job id: "+response.task_id
        	$('#result-trace').css('display','block')
            $('#result-report').text(report)
        	$('#bar-growth').width(percent.toString()+'%')
        }
    });
    if(percent === report) {
        clearInterval(event_id)
    }
    return
}



window.onload = tracejob;
var event_id = window.setInterval(tracejob, interval);