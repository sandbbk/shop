
    $(document).ready(function () {
        $("#btn").click(function() {
            $.ajax({
                url: document.getElementById('url').value,
                type: 'POST',
                async: true,
                dataType: 'json',
                data: $('#aj_form').serialize(),
                success: function(data) {
                        if (document.getElementById('url').value == 'login') {
                        document.getElementById('info').innerHTML = "<a href='{% url \"logout\" %}?next={{request.path}}'>Logout</a><p>You are logged as" + JSON.stringify(data.response) + ".</p>";
                        }
                        else if (document.getElementById('url').value == 'logout') {
                        document.getElementById('info').innerHTML = '';
                        }
                        else {
                        document.getElementById('aj_ch').innerHTML = JSON.stringify(data.response);
                        }
                },
                    error: function (xhr, ajaxOptions, thrownError) {
                        document.getElementById('aj_ch').innerHTML = xhr.status + " " + thrownError;

                },
            });
        });
    });

