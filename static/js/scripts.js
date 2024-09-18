function openCity(evt, cityName) {
    // Declare all variables
    var i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the link that opened the tab
    document.getElementById(cityName).style.display = "block";
    evt.currentTarget.className += " active";
}
jsPlumb.ready(function() {

    jsPlumb.setContainer($('.flowchart'))
    var common = {
        anchor:"Continuous",
        endpoint:["Rectangle", { width:20, height:20 }],
        paintStyle: {fill:"gray", stroke:"gray", strokeWidth:3}
    };
    var i = 0;
    var source_ids = [];
    var target_ids = [];

    source = [];
    target = [];

    $('.task-item').each(function() {
       source.push(this.id)
    });

    $('.vo-item').each(function() {
       target.push(this.id)
    });

    console.log(source)


     jsPlumb.makeSource(source, {
        connector: 'StateMachine'
    }, common);
    jsPlumb.makeTarget(target, {
        connector: 'StateMachine',
        allowLoopback: true,
        maxConnection:3,
        isTarget:true,
        overlays:[
            ["Arrow" , { width:12, length:12, location:0.67 }]
        ]


    }, common);

    jsPlumb.bind('connection', function(info) {
    console.log("before posting");
    $.get(save_url_val, { from: info.sourceId.split("-")[1], to: info.targetId.split("-")[1] });
    }

);

});




$(function() {

      // Modal Bind Functions
    $('#taskModal').on('hide.bs.modal show.bs.modal', function(event) {
        var $activeElement = $(document.activeElement);

  if ($activeElement.is('[data-toggle], [data-dismiss]')) {
        if (event.type === 'hide') {
      // Do something with the button that closed the modal
            console.log('The button that closed the modal is: ', $activeElement);

        }

    if (event.type === 'show') {
      // Do something with the button that opened the modal
      console.log('The button that opened the modal is: ', $activeElement);
      $('#discardTask').on('click', function () {
          console.log("Discard button clicked")
          $activeElement.closest('tr').remove()
          $('#taskModal').modal('toggle');

          // $.ajax({
          //       type: "POST",
          //       taskName: currentTask,
          //       url: discardURL,
          //       flag:tFlag,
          //       success: function (resp) {
          //           var htmMark = '';
          //           for(var i =0; i<resp.length; i++) {
          //
          //               var ind = resp[i].toString().split(",")[0];
          //               var val = resp[i].toString().split(",")[1];
          //
          //               htmMark += "<option value="+ind+">"+val+"</option>";
          //           }
          //           //dropdown.mserv.attr('enabled', 'enabled');
          //           $('#select_mservice').html(htmMark)
          //       }
          //   });

      });
    }
  }
});

    $('.spinner').hide();
    $('a.deploy').bind('click', function() {
        $(this).text('Deploying');
        url = $(this).attr('href');
        console.log("this url==="+url);
         URLArr = url.split('?');
         mainURL = URLArr[0];
         task = URLArr[1].split('=')[1];
         console.log(task)

        console.log("main   "+mainURL)
         id = $(this).attr('id');
         $('#spinner-'+id).show();
        $.ajax({
              type: "GET",
              dataType: 'json',
              data: {'id': id, 'task':task},
              crossDomain:true,
              url: mainURL
        }).done(function (data) {
            $('#spinner-'+id).hide();

            if(data) {
                console.log(data[0].timestamp);
                $('#spinner-'+id).parent().next().html("Reading Time: "+data[0].timestamp+"<br />Sensor Value: "+data[1].sensor_val);
                $('#'+id).text('Deployed');
                $('#'+id).addClass('btn-danger')
                $('#'+id).attr('href','#');
            }
        }).fail(function(data) {

            $('#spinner-'+id).parent().next().html("Error Accessing IoT Gateway!");
        });


        // console.log(url)
        // console.log(id)
        //
        //
        // $.get(url, {id: id}, function(data) {
        // $("#result").text(data.result);
        // });

        return false;
    });



    // jQuery selection for the 2 select boxes
    var dropdown = {
        service: $('#select_service'),
        mserv: $('#select_mservice')
    };

    // call to update on load
    updateMicroservices();

    // function to call XHR and update county dropdown
    function updateMicroservices() {
        var send = {
            service: dropdown.service.val()
        };
        //dropdown.mserv.attr('disabled', 'disabled');
        dropdown.mserv.empty();

       // $("#select_service").change(function () {
            //let user_identifier = this.value;
        console.log(send)
        $.ajax({
                type: "GET",
                url:url_val,
                data: send,
                success: function (resp) {
                    var htmMark = '';
                    for(var i =0; i<resp.length; i++) {

                        var ind = resp[i].toString().split(",")[0];
                        var val = resp[i].toString().split(",")[1];

                        htmMark += "<option value="+ind+">"+val+"</option>";
                    }
                    //dropdown.mserv.attr('enabled', 'enabled');
                    $('#select_mservice').html(htmMark)
                }
            });
       // });





    }

    // event listener to state dropdown change
    dropdown.service.on('change', function() {
        console.log("changed");
        updateMicroservices();
    });




  });

