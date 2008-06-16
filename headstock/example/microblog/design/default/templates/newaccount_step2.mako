<%include file="/header.mako"/>
  <body>
    <div id="doc" class="yui-t3">
      <div id="hd"><span id="headerlogo">speak up</span></div>
      <div id="bd">
	<div id="yui-main"><div>
	    <span>Now that you have authentified against your OpenID provider you can create an account by filling the form below. It may be pre-populated from your OpenID details if you have set them.</span>
</div>
	  <br />
	  %if error is not UNDEFINED:
	  <div>
	    <span class="error-message">
	      ${error}
	    </span>
	  </div>
	  <br />
	  % endif
	  <div class="persona-data">
	    <form action="/signup/complete" method="post">
	      <label for="username">Username:</label>
	      <input type="text" value="${username}" name="username" id="username" />	
	      <input type="submit" value="Complete"/>
	  </div>
	  </form>
	</div>
      </div>
      <div id="ft">
	<a rel="license" href="http://creativecommons.org/licenses/by-sa/3.0/">
	  <img alt="Creative Commons License" style="border-width:0" src="http://i.creativecommons.org/l/by-sa/3.0/80x15.png"/>
	</a>
	2008 Sylvain Hellegouarch
      </div>
    </div>
  </body>
<%include file="/footer.mako"/>
