var interval = 2000;

//send request to check job process
function tracejob() {

    $.ajax({
        url: "/trace_test",
        dataType : "json",
        data: {
        	// task_id: job_id,
        },
        success:  function(response) {
        	console.log(response)
        }
    });
    return
}



window.onload = tracejob;
window.setInterval(tracejob, interval);


function peek_profile(profile){
    $.ajax({
        url: "/", // url need ot config
        dataType : "json",
        data: {
            p_nmae: profile,
        },
        success:  function(response) {
            
        }
    });
    return
}