<%include file="/header.mako"/>
  <body>
    <div id="doc" class="yui-t3">
      <div id="hd"><span id="headerlogo">speak up</span></div>
      <div id="bd">
	<div id="yui-main">
	  <div id="container-1">
            <ul>
              <li><a href="#signin"><span>Sign in</span></a></li>
            </ul>
            <div id="signin">
	      <form action="/profile" method="get">
		<input type="text" name="openid_url" size="150" id="openid-identifier"/>
		<input type="submit" value="Sign in" />
	      </form>
            </div>
	  </div>
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
  
