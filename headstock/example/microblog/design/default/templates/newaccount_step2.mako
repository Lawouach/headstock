<div>
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
