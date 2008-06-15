<%!
    from microblog.utils import format_date
%>

% for member in collection.iter_members(0, 10):
  <div class="bubble">
     <blockquote>
	<p>${unicode(member.atom.entry.content)}</p>
     </blockquote>
     <cite><strong>${unicode(member.atom.entry.author.name)}</strong> on ${format_date(str(member.atom.entry.published))}</cite>
  </div>
% endfor