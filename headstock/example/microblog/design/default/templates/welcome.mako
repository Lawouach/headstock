<%include file="/header.mako"/>
  <body>
    <div id="doc" class="yui-t3">
      <div id="hd">
	<span id="headerlogo">speak up</span>
      </div>
      <div id="bd">
	<div id="yui-main"><div>
	    Welcome to Speak Up!

	    This small demo offers some possibilities about enhancing user experience over the web by integrating regular web applications with instant messaging applications (<a href="/help" title="speak up commands">see the available commands</a>). This means a greater interactivity for users.
	</div>	

	  <div>
	    If you want to try it out you may create an account by providing your OpenID below:
	  </div>
	  <br />
	  <div id="signin">
	    <form action="/signup/" method="get">
	      <input type="text" name="openid_url" size="150" id="openid-identifier"/>
	      <input type="submit" value="Sign up" />
	    </form>
	  </div>
	    
	</div>
      </div>
      <div id="ft">
	<span id="footerrights">
	  <a rel="license" href="http://creativecommons.org/licenses/by-sa/3.0/">
	    <img alt="Creative Commons License" style="border-width:0" src="http://i.creativecommons.org/l/by-sa/3.0/80x15.png"/>
	  </a>
	<br />
	  2008 Sylvain Hellegouarch
	</span>
      </div>
    </div>  
  </body>
<%include file="/footer.mako"/>
