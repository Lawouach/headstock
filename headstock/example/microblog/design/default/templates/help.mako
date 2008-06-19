<%include file="/header.mako"/>
  <body>
    <div id="doc" class="yui-t3">
      <div id="hd">
	<span id="headerlogo">speak up</span>
      </div>
      <div id="bd">
	<div id="yui-main">
	  <span style="display:block;">Available commands:</span>
	  <br />
	  <table>
	    <tbody>
	      <tr>
		<td>Publish</td>
		<td><pre>PI text</pre></td>
	      </tr>
	      <tr>
		<td>Publish to a node</td>
		<td><pre>PI [node] text</pre></td>
	      </tr>
	      <tr>
		<td>Delete</td>
		<td><pre>DI itemId</pre></td>
	      </tr>
	      <tr>
		<td>Delete from a node</td>
		<td><pre>DI [node] itemId</pre></td>
	      </tr>
	      <tr>
		<td>Create a node</td>
		<td><pre>CN node</pre></td>
	      </tr>
	      <tr>
		<td>Delete a node</td>
		<td><pre>DN node</pre></td>
	      </tr>
	      <tr>
		<td>Purge a node</td>
		<td><pre>PN node</pre></td>
	      </tr>
	      <tr>
		<td>Subscribe to a node</td>
		<td><pre>SN node</pre></td>
	      </tr>
	      <tr>
		<td>Unsubscribe from a node</td>
		<td><pre>UN node</pre></td>
	      </tr>
	    </tbody>
	    <thead>
	      <tr>
		<th>Action</th>
		<th>Command</th>
	      </tr>
	    </thead>
	  </table>
	</div>
      </div>
      <div id="ft">
	<a rel="license" href="http://creativecommons.org/licenses/by-sa/3.0/">
	  <img alt="Creative Commons License" style="border-width:0" src="http://i.creativecommons.org/l/by-sa/3.0/80x15.png"/>
	</a>
	<br />
	2008 Sylvain Hellegouarch
      </div>
    </div>
  </body>
<%include file="/footer.mako"/>
