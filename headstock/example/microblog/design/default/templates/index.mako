<%include file="/header.mako"/>
  <body>
    <div id="doc" class="yui-t3">
      <div id="hd">
	<!-- PUT MASTHEAD CODE HERE -->
      </div>
      <div id="bd">
	<div id="yui-main">
	    <div id="container-1">
              <ul>
                <li><a href="#speakup"><span>Speak up</span></a></li>
	        %if context.get('profiletpl'):
                    <li><a href="#profile"><span>Profile</span></a></li>
		%endif
              </ul>
              <div id="speakup">
	        %if context.get('speakuptpl'):
		    <%include file="${context.get('speakuptpl')}" />
		%endif
              </div>
	      %if context.get('profiletpl'):
              <div id="profile">
		  <%include file="${context.get('profiletpl')}" />
	      </div>
	      %endif
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
