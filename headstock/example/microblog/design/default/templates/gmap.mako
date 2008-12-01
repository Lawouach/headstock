<script src="http://maps.google.com/maps?file=api&amp;v=2&amp;key=ABQIAAAAHJGcSVDQRQ3suKJmVt9Q5BTwM0brOpm-All5BF6PoaKBxRWWERR7tHWQw8TALw7VlFkTahW8xNyMUg" type="text/javascript"> </script>
<script type="text/javascript">
   //<![CDATA[
   function load_map(long, lat) {
      if (GBrowserIsCompatible()) {
          var map = new GMap2(document.getElementById("map"));
          map.setCenter(new GLatLng(long, lat), 13);
      }
   }

   //]]>
</script>