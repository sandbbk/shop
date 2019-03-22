
    $(document).ready(function () {
        $("#btn").click(function() {
            $.ajax({
                url: document.getElementById('url').value,
                type: 'POST',
                async: true,
                dataType: 'json',
                data: $('#aj_form').serialize(),
                success: function(data) {
                    document.getElementById('aj_ch').innerHTML = JSON.stringify(data.response);
                },
                    error: function (xhr, ajaxOptions, thrownError) {
                        document.getElementById('aj_ch').innerHTML = xhr.status + thrownError

                }
            });
        });
    });

