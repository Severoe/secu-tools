function editProfile(os, compiler, version, name) {
    console.log(os, compiler, version, name)
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
            
        }
    });
}

function editCompiler(row) {
    var id = '#' + row
    var tr = $(id).closest('tr')
    var os = tr.find('td.os').text()
    var compiler = tr.find('td.compiler').text()
    var version = tr.find('td.version').text()
    $.ajax({
        type: 'POST',
        url: "/getProfile",
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