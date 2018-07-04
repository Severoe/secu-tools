function editProfile(os, compiler, version, name) {
    document.getElementById('update_profile').style.visibility = 'visible'
    $.ajax({
        type: 'POST',
        url: "/getProfile",
        dataType: "json",
        data: {
            target_os: os,
            compiler: compiler,
            version: version,
            name: name,
        },
        success: function (response) {
            console.log(response)
            $('#target_os').append(response['target_os'])
        }
    });
}

function editCompiler(os, compiler, version) {
    $.ajax({
        type: 'POST',
        url: "/getCompiler",
        dataType: "json",
        data: {
            target_os: os,
            compiler: compiler,
            version: version,
        },
        success: function (response) {

        }
    });
}