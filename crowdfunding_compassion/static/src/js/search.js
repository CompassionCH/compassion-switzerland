$(document).ready(function(){
  $("#myInput").on("keyup", function() {
    var value = $(this).val().toLowerCase();
    var items = $(".card");
    //show only those matching user input:
      items.filter(function() {
          var is_show = $(this).text().toLowerCase().indexOf(value) > -1
          if (!is_show) {
              $(this).parent().css('display', 'none')
          } else {
              $(this).parent().css('display', 'block')
          }
    });
  });
});
console.log('Point of Sale JavaScript loaded');